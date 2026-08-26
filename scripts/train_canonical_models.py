import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
import joblib
import json
import os

def train_canonical_models():
    """
    Canonical Model Training Pipeline.
    Strictly enforces orthongonal feature selection:
    - 12M Default: Static + Current + Trajectory
    - 3M/6M Delinq & 12M Prep: Static + Current + Trajectory + Reliability
    """
    print("Loading prediction snapshots...")
    df = pd.read_parquet('data/processed/prediction_snapshots.parquet')
    
    period_int = df['period'].str[:4].astype(int)
    train_mask = period_int <= 2021
    valid_mask = (period_int >= 2022) & (period_int <= 2023)
    
    df_train = df[train_mask]
    df_valid = df[valid_mask]
    
    base_features = [
        'orig_fico', 'orig_ltv', 'orig_dti', 'orig_upb', 'orig_interest_rate', 
        'curr_upb', 'rem_months', 'curr_status', 'mod_flag', 'canonical_state', 
        'trajectory_dpd_6m_max', 'trajectory_state_transitions_6m', 
        'trajectory_consecutive_delinq', 'trajectory_balance_reduction_6m'
    ]
    
    targets = {
        'next_12m_default_flag': base_features,  # Explicitly excludes reliability_score
        'next_3m_delinquency_flag': base_features + ['reliability_score'],
        'next_6m_delinquency_flag': base_features + ['reliability_score'],
        'next_12m_prepayment_flag': base_features + ['reliability_score']
    }
    
    cat_cols = ['curr_status', 'mod_flag', 'canonical_state']
    
    for target, features in targets.items():
        print(f"Training {target}...")
        X_train = df_train[features].copy()
        y_train = df_train[target].fillna(0).astype(int)
        X_valid = df_valid[features].copy()
        y_valid = df_valid[target].fillna(0).astype(int)
        
        for col in cat_cols:
            X_train[col] = X_train[col].astype('category')
            X_valid[col] = X_valid[col].astype('category')
        for col in features:
            if col not in cat_cols:
                X_train[col] = pd.to_numeric(X_train[col], errors='coerce')
                X_valid[col] = pd.to_numeric(X_valid[col], errors='coerce')
                
        clf = lgb.LGBMClassifier(n_estimators=50, random_state=42, n_jobs=-1, class_weight='balanced')
        clf.fit(X_train, y_train, eval_set=[(X_valid, y_valid)])
        
        calibrated = CalibratedClassifierCV(clf, method='sigmoid', cv="prefit")
        calibrated.fit(X_valid, y_valid)
        
        out_dir = f'models/{target}'
        os.makedirs(out_dir, exist_ok=True)
        joblib.dump(calibrated, f'{out_dir}/model.pkl')
        with open(f'{out_dir}/features.json', 'w') as f:
            json.dump(features, f)

if __name__ == '__main__':
    train_canonical_models()
