import pandas as pd
import numpy as np
import glob
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    files = glob.glob('data/processed/canonical_panel_*.parquet')
    dfs = []
    for f in files:
        dfs.append(pd.read_parquet(f))
    df = pd.concat(dfs, ignore_index=True)
    
    # Load reliability
    rel = pd.read_parquet('data/processed/reliability_scores.parquet')
    df = df.merge(rel[['loan_id', 'reliability_score', 'reliability_band']], on='loan_id', how='left')
    return df

def derive_targets(df):
    logging.info("Deriving targets (optimized)...")
    df = df.sort_values(['loan_id', 'period']).reset_index(drop=True)
    
    state_map = {
        'CURRENT': 0, '30_DPD': 1, '60_DPD': 2, '90_PLUS_DPD': 3, 
        'PREPAID': -1, 'DEFAULT': 4, 'OTHER_TERMINAL': -2, 'UNKNOWN': 0
    }
    df['state_num'] = df['canonical_state'].map(state_map)
    
    df['next_state'] = df['canonical_state'].shift(-1)
    df.loc[df['loan_id'] != df['loan_id'].shift(-1), 'next_state'] = np.nan
    df['eligible_next_state'] = df['next_state'].notna().astype(int)
    
    is_delinq = (df['state_num'] >= 1).astype(float)
    is_default = (df['state_num'] == 4).astype(float)
    is_prepaid = (df['state_num'] == -1).astype(float)
    
    # Fast lookahead using shift
    # For 12 months, we can just sum 1 to 12 shifts
    def get_future_sums(series, k):
        res_sum = np.zeros(len(df))
        res_count = np.zeros(len(df))
        for i in range(1, k+1):
            s = series.shift(-i)
            # Mask out boundaries
            valid = (df['loan_id'] == df['loan_id'].shift(-i))
            res_sum += np.where(valid & s.notna(), s, 0)
            res_count += np.where(valid, 1, 0)
        return res_sum, res_count
        
    df['future_3m_delinq_sum'], df['future_3m_count'] = get_future_sums(is_delinq, 3)
    df['future_6m_delinq_sum'], df['future_6m_count'] = get_future_sums(is_delinq, 6)
    df['future_12m_default_sum'], df['future_12m_count'] = get_future_sums(is_default, 12)
    df['future_12m_prepaid_sum'], _ = get_future_sums(is_prepaid, 12)
    
    df['next_3m_delinquency_flag'] = (df['future_3m_delinq_sum'] > 0).astype(int)
    df['next_6m_delinquency_flag'] = (df['future_6m_delinq_sum'] > 0).astype(int)
    df['next_12m_default_flag'] = (df['future_12m_default_sum'] > 0).astype(int)
    df['next_12m_prepayment_flag'] = (df['future_12m_prepaid_sum'] > 0).astype(int)
    
    last_state = df.groupby('loan_id')['state_num'].transform('last')
    is_terminal = last_state.isin([-1, -2, 4])
    
    df['eligible_3m_delinquency'] = ((df['next_3m_delinquency_flag'] == 1) | (df['future_3m_count'] == 3) | is_terminal).astype(int)
    df['eligible_6m_delinquency'] = ((df['next_6m_delinquency_flag'] == 1) | (df['future_6m_count'] == 6) | is_terminal).astype(int)
    df['eligible_12m_default'] = ((df['next_12m_default_flag'] == 1) | (df['future_12m_count'] == 12) | is_terminal).astype(int)
    df['eligible_12m_prepayment'] = ((df['next_12m_prepayment_flag'] == 1) | (df['future_12m_count'] == 12) | is_terminal).astype(int)
    
    df.loc[df['eligible_3m_delinquency'] == 0, 'next_3m_delinquency_flag'] = np.nan
    df.loc[df['eligible_6m_delinquency'] == 0, 'next_6m_delinquency_flag'] = np.nan
    df.loc[df['eligible_12m_default'] == 0, 'next_12m_default_flag'] = np.nan
    df.loc[df['eligible_12m_prepayment'] == 0, 'next_12m_prepayment_flag'] = np.nan
    
    return df

def derive_trajectory_features(df):
    logging.info("Deriving trajectory features (optimized)...")
    
    state_num = df['state_num'].astype(float)
    # Fast 6m max
    res_max = state_num.copy().values
    for i in range(1, 6):
        s = state_num.shift(i)
        valid = (df['loan_id'] == df['loan_id'].shift(i))
        # use np.fmax which handles NaNs
        res_max = np.where(valid, np.fmax(res_max, s.fillna(-np.inf)), res_max)
    df['trajectory_dpd_6m_max'] = res_max
    
    # State transitions
    state_changed = (df['canonical_state'] != df['canonical_state'].shift(1)).astype(float)
    state_changed.loc[df['loan_id'] != df['loan_id'].shift(1)] = 0
    
    res_sum = state_changed.copy().values
    for i in range(1, 6):
        s = state_changed.shift(i)
        valid = (df['loan_id'] == df['loan_id'].shift(i))
        res_sum += np.where(valid, s.fillna(0), 0)
    df['trajectory_state_transitions_6m'] = res_sum
    
    # Consecutive delinquency
    delinq_mask = (df['state_num'] >= 1)
    df['delinq_block'] = (~delinq_mask).groupby(df['loan_id']).cumsum()
    df['trajectory_consecutive_delinq'] = df.groupby(['loan_id', 'delinq_block']).cumcount() + 1
    df.loc[~delinq_mask, 'trajectory_consecutive_delinq'] = 0
    
    # Balance reduction
    df['curr_upb_num'] = pd.to_numeric(df['curr_upb'], errors='coerce')
    upb_6m_ago = df['curr_upb_num'].shift(6)
    valid = (df['loan_id'] == df['loan_id'].shift(6))
    df['trajectory_balance_reduction_6m'] = np.where(valid, upb_6m_ago - df['curr_upb_num'], np.nan)
    
    return df

def run_phase3():
    df = load_data()
    df = derive_targets(df)
    df = derive_trajectory_features(df)
    
    # Select columns for snapshot
    static_cols = ['orig_fico', 'orig_ltv', 'orig_dti', 'orig_upb', 'orig_interest_rate', 'prop_state', 'prop_type', 'loan_purpose', 'first_payment_date']
    current_cols = ['curr_upb', 'rem_months', 'curr_status', 'mod_flag', 'canonical_state', 'zb_code']
    traj_cols = ['trajectory_dpd_6m_max', 'trajectory_state_transitions_6m', 'trajectory_consecutive_delinq', 'trajectory_balance_reduction_6m']
    rel_cols = ['reliability_score', 'reliability_band']
    elig_cols = ['eligible_3m_delinquency', 'eligible_6m_delinquency', 'eligible_12m_default', 'eligible_12m_prepayment', 'eligible_next_state']
    target_cols = ['next_3m_delinquency_flag', 'next_6m_delinquency_flag', 'next_12m_default_flag', 'next_12m_prepayment_flag', 'next_state']
    
    snapshot_cols = ['loan_id', 'period'] + static_cols + current_cols + traj_cols + rel_cols + elig_cols + target_cols
    
    snapshot_df = df[snapshot_cols].copy()
    
    # Output snapshot
    snapshot_df.to_parquet('data/processed/prediction_snapshots.parquet', index=False)
    
    # Target summary
    summary = []
    for tgt in ['3m_delinquency', '6m_delinquency', '12m_default', '12m_prepayment']:
        elig_col = f'eligible_{tgt}'
        flag_col = f'next_{tgt}_flag'
        total = len(snapshot_df)
        eligible = snapshot_df[elig_col].sum()
        censored = total - eligible
        positive = snapshot_df[flag_col].sum()
        negative = eligible - positive
        prevalence = positive / eligible if eligible > 0 else 0
        
        summary.append({
            'target': flag_col,
            'total_snapshots': total,
            'eligible': eligible,
            'censored': censored,
            'positive': positive,
            'negative': negative,
            'prevalence': prevalence
        })
        
    summary_df = pd.DataFrame(summary)
    summary_df.to_parquet('data/processed/target_summary.parquet', index=False)
    
    print(summary_df.to_string())
    logging.info("Phase 3 complete.")

if __name__ == '__main__':
    run_phase3()
