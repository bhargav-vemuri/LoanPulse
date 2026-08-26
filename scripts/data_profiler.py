import glob
import pandas as pd
import json
import os
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_profiling():
    parquet_files = glob.glob('data/processed/canonical_panel_*.parquet')
    
    # We will sample to avoid memory issues if total size is huge, 
    # but since these are 'sample' datasets, they might fit in memory.
    # Let's read them into a single dataframe for robust profiling.
    dfs = []
    for pf in parquet_files:
        df = pd.read_parquet(pf, columns=[
            'loan_id', 'period', 'orig_fico', 'orig_ltv', 'orig_dti', 'orig_upb', 
            'curr_upb', 'rem_months', 'curr_status', 'mod_flag', 'canonical_state', 'zb_code'
        ])
        # add vintage year based on filename
        vintage = os.path.basename(pf).replace('canonical_panel_', '').replace('.parquet', '')
        df['vintage'] = vintage
        dfs.append(df)
        
    full_df = pd.concat(dfs, ignore_index=True)
    
    # 7. Missingness intelligence
    # by feature
    missing_by_feature = full_df.isnull().mean().to_dict()
    # by vintage
    missing_by_vintage = full_df.groupby('vintage').apply(lambda x: x.isnull().mean().to_dict()).to_dict()
    
    # 8. Distribution profiling
    # Let's pick a few numeric ones
    num_cols = ['orig_fico', 'orig_ltv', 'orig_dti', 'orig_upb', 'curr_upb']
    for col in num_cols:
        full_df[col] = pd.to_numeric(full_df[col], errors='coerce')
        
    dist_stats = full_df[num_cols].describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).to_dict()
    
    # 9. Relationship checks
    # curr_upb > orig_upb grouped by mod_flag
    rel_upb = full_df.groupby('mod_flag').apply(lambda x: (x['curr_upb'] > x['orig_upb']).mean()).to_dict()
    
    # 10. Preliminary drift analysis
    # Average FICO by vintage
    drift_fico = full_df.groupby('vintage')['orig_fico'].mean().to_dict()
    
    report = {
        "missingness": {
            "overall": missing_by_feature,
            "by_vintage": missing_by_vintage
        },
        "distributions": dist_stats,
        "relationships": {
            "pct_curr_upb_gt_orig_upb_by_mod_flag": rel_upb
        },
        "drift": {
            "mean_fico_by_vintage": drift_fico
        }
    }
    
    os.makedirs('reports', exist_ok=True)
    with open('reports/profiling_summary.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    logging.info("Profiling complete.")
    print("Drift - Mean FICO by Vintage:")
    print(json.dumps(drift_fico, indent=2))

if __name__ == '__main__':
    run_profiling()
