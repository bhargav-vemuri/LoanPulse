import pandas as pd
import numpy as np
import json
import glob
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_psi(expected, actual, buckets=10):
    def build_buckets(data, num_buckets):
        return pd.qcut(data, q=num_buckets, duplicates='drop', retbins=True)[1]
    
    expected = pd.to_numeric(expected, errors='coerce').dropna()
    actual = pd.to_numeric(actual, errors='coerce').dropna()
    
    if len(expected) == 0 or len(actual) == 0:
        return np.nan
        
    bins = build_buckets(expected, buckets)
    bins = np.concatenate(([-np.inf], bins[1:-1], [np.inf]))
    
    expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)
    
    def sub_psi(e_perc, a_perc):
        if a_perc == 0:
            a_perc = 0.0001
        if e_perc == 0:
            e_perc = 0.0001
        return (e_perc - a_perc) * np.log(e_perc / a_perc)
    
    psi_value = np.sum(sub_psi(expected_percents[i], actual_percents[i]) for i in range(len(expected_percents)))
    return psi_value

def investigate_rules(evidence_df):
    logging.info("Investigating VAL_007 (Period < First Payment Date)...")
    val_007_count = len(evidence_df[evidence_df['rule_id'] == 'VAL_007'])
    # Classification: STRUCTURAL_EXPECTED
    # Rationale: Mortgage reporting often begins in the origination/funding month, prior to the first scheduled payment.
    
    logging.info("Investigating VAL_002 (Curr UPB > Orig UPB w/o Mod)...")
    val_002_count = len(evidence_df[evidence_df['rule_id'] == 'VAL_002'])
    # Classification: SOFT_WARNING
    # Rationale: Can occur via capitalized advances, escrow shortages, or undocumented modifications.
    
    logging.info("Investigating VAL_003 (Missing FICO)...")
    val_003_evidence = evidence_df[evidence_df['rule_id'] == 'VAL_003']
    val_003_loans = val_003_evidence['loan_id'].nunique()
    val_003_obs = len(val_003_evidence)
    # Classification: STRUCTURAL_EXPECTED / INFORMATIONAL
    
    logging.info("Investigating VAL_006 (Delinquency Gap)...")
    val_006_count = len(evidence_df[evidence_df['rule_id'] == 'VAL_006'])
    # Classification: DATA_QUALITY_SIGNAL

    return {
        'VAL_007_count': val_007_count,
        'VAL_002_count': val_002_count,
        'VAL_003_loans': val_003_loans,
        'VAL_003_obs': val_003_obs,
        'VAL_006_count': val_006_count
    }

def compute_drift(canonical_dfs):
    logging.info("Computing Drift...")
    # Using 2018 as baseline (expected)
    df_2018 = pd.concat([df for df in canonical_dfs if df['vintage'].iloc[0] == '2018'])
    
    drift_metrics = []
    
    features = ['orig_fico', 'orig_ltv', 'orig_dti']
    
    for df in canonical_dfs:
        vintage = df['vintage'].iloc[0]
        if vintage == '2018': continue
        
        for f in features:
            psi = calculate_psi(df_2018[f], df[f])
            severity = "LOW"
            if psi > 0.1: severity = "MODERATE"
            if psi > 0.2: severity = "HIGH"
            
            interpretation = "Stable"
            if severity == "HIGH": interpretation = f"Significant population shift in {f}"
            elif severity == "MODERATE": interpretation = f"Moderate population shift in {f}"
            
            drift_metrics.append({
                'feature': f,
                'period_a': '2018',
                'period_b': vintage,
                'metric': 'PSI',
                'metric_value': psi,
                'severity': severity,
                'interpretation': interpretation
            })
            
    return pd.DataFrame(drift_metrics)

def compute_reliability(evidence_df, full_df):
    logging.info("Computing Reliability...")
    
    # Map rules to taxonomy & penalty
    rule_taxonomy = {
        'VAL_001': {'taxonomy': 'TEMPORAL_INTEGRITY', 'penalty': 15, 'class': 'HARD_ERROR'},
        'VAL_002': {'taxonomy': 'BALANCE_CONSISTENCY', 'penalty': 5, 'class': 'SOFT_WARNING'},
        'VAL_003': {'taxonomy': 'ATTRIBUTE_COMPLETENESS', 'penalty': 2, 'class': 'INFORMATIONAL'},
        'VAL_004': {'taxonomy': 'ATTRIBUTE_COMPLETENESS', 'penalty': 10, 'class': 'HARD_ERROR'},
        'VAL_005': {'taxonomy': 'STATE_CONSISTENCY', 'penalty': 20, 'class': 'HARD_ERROR'},
        'VAL_006': {'taxonomy': 'TRAJECTORY_INTEGRITY', 'penalty': 10, 'class': 'DATA_QUALITY_SIGNAL'},
        'VAL_007': {'taxonomy': 'REPORTING_CONVENTION', 'penalty': 0, 'class': 'STRUCTURAL_EXPECTED'},
        'VAL_008': {'taxonomy': 'STATE_CONSISTENCY', 'penalty': 20, 'class': 'HARD_ERROR'}
    }
    
    # Create penalty df
    penalties = evidence_df.copy()
    penalties['penalty'] = penalties['rule_id'].map(lambda x: rule_taxonomy.get(x, {}).get('penalty', 0))
    penalties['quality_category'] = penalties['rule_id'].map(lambda x: rule_taxonomy.get(x, {}).get('taxonomy', 'UNKNOWN'))
    
    # Apply recency weighting
    # Sort loan periods to find max period per loan
    max_periods = full_df.groupby('loan_id')['period'].max().reset_index().rename(columns={'period': 'max_period'})
    penalties = penalties.merge(max_periods, on='loan_id', how='left')
    
    # For simplicity, if reporting_month is within 12 months of max_period, weight = 1.0, else 0.5
    def calc_weight(row):
        try:
            m_curr = int(row['reporting_month'][:4]) * 12 + int(row['reporting_month'][4:])
            m_max = int(row['max_period'][:4]) * 12 + int(row['max_period'][4:])
            if (m_max - m_curr) <= 12: return 1.0
            return 0.5
        except:
            return 1.0
            
    penalties['recency_weight'] = penalties.apply(calc_weight, axis=1)
    penalties['weighted_penalty'] = penalties['penalty'] * penalties['recency_weight']
    
    # Aggregate to loan level
    loan_penalties = penalties.groupby('loan_id')['weighted_penalty'].sum().reset_index()
    
    # Initialize all loans to 100
    loans = pd.DataFrame({'loan_id': full_df['loan_id'].unique()})
    scores = loans.merge(loan_penalties, on='loan_id', how='left').fillna(0)
    
    scores['reliability_score'] = 100 - scores['weighted_penalty']
    scores['reliability_score'] = scores['reliability_score'].clip(lower=0, upper=100)
    
    # Banding
    def assign_band(score):
        if score >= 90: return 'HIGH'
        if score >= 70: return 'MEDIUM'
        return 'LOW'
        
    scores['reliability_band'] = scores['reliability_score'].apply(assign_band)
    
    return scores, penalties

def run_phase2():
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    evidence_df = pd.read_parquet('data/processed/validation_evidence.parquet')
    parquet_files = glob.glob('data/processed/canonical_panel_*.parquet')
    
    dfs = []
    for pf in parquet_files:
        df = pd.read_parquet(pf, columns=[
            'loan_id', 'period', 'orig_fico', 'orig_ltv', 'orig_dti'
        ])
        df['vintage'] = os.path.basename(pf).replace('canonical_panel_', '').replace('.parquet', '')
        dfs.append(df)
        
    full_df = pd.concat(dfs, ignore_index=True)
    
    rule_stats = investigate_rules(evidence_df)
    
    drift_df = compute_drift(dfs)
    drift_df.to_parquet('data/processed/drift_metrics.parquet', index=False)
    
    scores_df, enriched_evidence = compute_reliability(evidence_df, full_df)
    scores_df.to_parquet('data/processed/reliability_scores.parquet', index=False)
    enriched_evidence.to_parquet('data/processed/reliability_evidence.parquet', index=False)
    
    # Output distributions
    dist = scores_df['reliability_score'].describe().to_dict()
    bands = scores_df['reliability_band'].value_counts(normalize=True).to_dict()
    
    with open('reports/phase2_summary.json', 'w') as f:
        json.dump({
            'rule_stats': rule_stats,
            'reliability_distribution': dist,
            'reliability_bands': bands
        }, f, indent=2)
        
    logging.info("Phase 2 complete.")

if __name__ == '__main__':
    run_phase2()
