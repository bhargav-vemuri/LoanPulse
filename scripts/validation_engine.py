import glob
import pandas as pd
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_validation():
    with open('configs/validation_rules.json', 'r') as f:
        rules_config = json.load(f)
    rules = rules_config['rules']
    
    parquet_files = glob.glob('data/processed/canonical_panel_*.parquet')
    all_violations = []
    
    for pf in parquet_files:
        logging.info(f"Validating {pf}")
        df = pd.read_parquet(pf)
        
        # We need lag variables for some rules
        # Sort by loan_id and period
        df = df.sort_values(['loan_id', 'period'])
        
        # Create lags
        df['lag_status_num'] = pd.to_numeric(df['curr_status'].replace({'R': '99', 'RA': '99', 'XX': '-1', '': '-1'}), errors='coerce').shift(1)
        df['curr_status_num'] = pd.to_numeric(df['curr_status'].replace({'R': '99', 'RA': '99', 'XX': '-1', '': '-1'}), errors='coerce')
        df['lag_zb_code'] = df.groupby('loan_id')['zb_code'].shift(1)
        
        # Rule evaluation
        for rule in rules:
            rule_id = rule['rule_id']
            # safely evaluate
            try:
                # Need to convert strings to numbers for some checks
                if rule_id == 'VAL_002':
                    df['curr_upb_num'] = pd.to_numeric(df['curr_upb'], errors='coerce')
                    df['orig_upb_num'] = pd.to_numeric(df['orig_upb'], errors='coerce')
                    mask = (df['curr_upb_num'] > df['orig_upb_num']) & (df['mod_flag'] != 'Y')
                elif rule_id == 'VAL_001':
                    df['rem_months_num'] = pd.to_numeric(df['rem_months'], errors='coerce')
                    mask = (df['rem_months_num'] < 0)
                elif rule_id == 'VAL_003':
                    mask = df['orig_fico'].isna() | (df['orig_fico'] == 9999)
                elif rule_id == 'VAL_004':
                    mask = df['orig_ltv'].isna() | (df['orig_ltv'] == 999)
                elif rule_id == 'VAL_005':
                    df['curr_upb_num'] = pd.to_numeric(df['curr_upb'], errors='coerce')
                    mask = df['zb_code'].notna() & (df['curr_upb_num'] > 0)
                elif rule_id == 'VAL_006':
                    # Only valid for same loan_id
                    mask = (df['loan_id'] == df['loan_id'].shift(1)) & ((df['curr_status_num'] - df['lag_status_num']) > 1) & (df['curr_status_num'] < 99)
                elif rule_id == 'VAL_007':
                    # First payment date is YYYYMM. Period is YYYYMM.
                    mask = (pd.to_numeric(df['period'], errors='coerce') < pd.to_numeric(df['first_payment_date'], errors='coerce'))
                elif rule_id == 'VAL_008':
                    mask = (df['loan_id'] == df['loan_id'].shift(1)) & df['lag_zb_code'].notna()
                else:
                    mask = pd.Series([False]*len(df))
                    
                violations = df[mask]
                
                if len(violations) > 0:
                    for _, row in violations.iterrows():
                        observed_values = {f: row.get(f) for f in rule['fields'] if f in row.index}
                        all_violations.append({
                            'loan_id': row['loan_id'],
                            'reporting_month': row['period'],
                            'rule_id': rule_id,
                            'severity': rule['severity'],
                            'affected_fields': json.dumps(rule['fields']),
                            'observed_values': json.dumps(observed_values),
                            'explanation': rule['description']
                        })
            except Exception as e:
                logging.error(f"Error evaluating rule {rule_id}: {e}")
                
    violations_df = pd.DataFrame(all_violations)
    os.makedirs('reports', exist_ok=True)
    if not violations_df.empty:
        violations_df.to_parquet('data/processed/validation_evidence.parquet', index=False)
        # Summarize violations
        summary = violations_df['rule_id'].value_counts().to_dict()
    else:
        summary = {}
        
    with open('reports/validation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
        
    logging.info("Validation complete.")
    print("Rule Violations:")
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    run_validation()
