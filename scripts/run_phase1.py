import os
import glob
import json
import zipfile
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_schema():
    with open('configs/schema.json', 'r') as f:
        return json.load(f)

def get_origination_dtypes():
    return {
        'loan_id': 'string',
        'orig_fico': 'Int64',
        'first_payment_date': 'string',
        'first_time_buyer': 'string',
        'maturity_date': 'string',
        'msa': 'string',
        'mi_pct': 'float32',
        'num_units': 'Int64',
        'occ_status': 'string',
        'orig_cltv': 'float32',
        'orig_dti': 'float32',
        'orig_upb': 'float32',
        'orig_ltv': 'float32',
        'orig_interest_rate': 'float32',
        'channel': 'string',
        'ppmt_penalty': 'string',
        'amort_type': 'string',
        'prop_state': 'string',
        'prop_type': 'string',
        'postal_code': 'string',
        'loan_purpose': 'string',
        'orig_loan_term': 'Int64',
        'num_borrowers': 'Int64',
        'seller_name': 'string',
        'super_conforming': 'string',
        'pre_harp_id': 'string',
        'program': 'string',
        'harp_indicator': 'string',
        'val_method': 'string',
        'io_indicator': 'string',
        'vantage_score': 'Int64'
    }

def get_performance_dtypes():
    return {
        'loan_id': 'string',
        'period': 'string',
        'curr_upb': 'float32',
        'curr_status': 'string',
        'loan_age': 'Int64',
        'rem_months': 'Int64',
        'defect_date': 'string',
        'mod_flag': 'string',
        'zb_code': 'string',
        'zb_date': 'string',
        'curr_int_rate': 'float32',
        'non_int_upb': 'float32',
        'ddlpi': 'string',
        'mi_rec': 'float32',
        'net_sales': 'string',
        'non_mi_rec': 'float32',
        'expenses': 'float32',
        'legal_costs': 'float32',
        'maint_costs': 'float32',
        'taxes_ins': 'float32',
        'misc_exp': 'float32',
        'actual_loss': 'float32',
        'cum_mod_costs': 'float32',
        'step_ind': 'string',
        'deferral_flag': 'string',
        'eltv': 'float32',
        'zb_removal_upb': 'float32',
        'delinq_acc_int': 'float32',
        'disaster_delinq': 'string',
        'assist_plan': 'string',
        'mod_cost': 'float32',
        'int_upb': 'float32',
        'mi_cancel': 'string',
        'servicer': 'string',
        'cramdown': 'float32'
    }

def map_origination(df, schema):
    # Rename columns explicitly
    df.columns = schema['origination_columns']
    
    # Map to logical names
    mapping = {
        'Loan Identifier': 'loan_id',
        'Classic FICO\u00ae': 'orig_fico',
        'First Payment Date': 'first_payment_date',
        'First Time Homebuyer Indicator': 'first_time_buyer',
        'Maturity Date': 'maturity_date',
        'Metropolitan Statistical Area (MSA) Or Metropolitan Division': 'msa',
        'Mortgage Insurance Percentage (MI %)': 'mi_pct',
        'Number of Units': 'num_units',
        'Occupancy Status': 'occ_status',
        'Original Combined Loan-to-Value (CLTV)': 'orig_cltv',
        'Original Debt-to-Income (DTI) Ratio': 'orig_dti',
        'Original UPB': 'orig_upb',
        'Original Loan-to-Value (LTV)': 'orig_ltv',
        'Original Interest Rate': 'orig_interest_rate',
        'Channel': 'channel',
        'Prepayment Penalty Indicator': 'ppmt_penalty',
        'Amortization Type': 'amort_type',
        'Property State': 'prop_state',
        'Property Type': 'prop_type',
        'Postal Code': 'postal_code',
        'Loan Purpose': 'loan_purpose',
        'Original Loan Term': 'orig_loan_term',
        'Number of Borrowers': 'num_borrowers',
        'Seller Name': 'seller_name',
        'Super Conforming Flag': 'super_conforming',
        'Pre-HARP Loan Sequence Number': 'pre_harp_id',
        'Special Eligibility Program': 'program',
        'HARP Indicator': 'harp_indicator',
        'Property Valuation Method': 'val_method',
        'Interest Only (I/O) Indicator': 'io_indicator',
        'VantageScore\u00ae 4.0': 'vantage_score'
    }
    df = df.rename(columns=mapping)
    
    # Clean up nulls
    for col in ['orig_fico', 'orig_dti', 'orig_ltv', 'orig_cltv', 'mi_pct']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace({'9999': np.nan, '999': np.nan, 9999: np.nan, 999: np.nan, '': np.nan}), errors='coerce')
            
    return df

def map_performance(df, schema):
    df.columns = schema['performance_columns']
    mapping = {
        'Loan Identifier': 'loan_id',
        'Period': 'period',
        'Current Actual UPB': 'curr_upb',
        'Current Loan Delinquency Status': 'curr_status',
        'Loan Age': 'loan_age',
        'Remaining Months to Legal Maturity': 'rem_months',
        'Underwriting Defect and Major Servicing Defect Settlement Date': 'defect_date',
        'Modification Flag': 'mod_flag',
        'Zero Balance Code': 'zb_code',
        'Zero Balance Effective Date': 'zb_date',
        'Current Interest Rate': 'curr_int_rate',
        'Current Non-Interest Bearing UPB': 'non_int_upb',
        'Due Date of Last Paid Installment (DDLPI)': 'ddlpi',
        'MI Recoveries': 'mi_rec',
        'Net Sales Proceeds': 'net_sales',
        'Non MI Recoveries': 'non_mi_rec',
        'Total Expenses': 'expenses',
        'Legal Costs': 'legal_costs',
        'Maintenance and Preservation Costs': 'maint_costs',
        'Taxes and Insurance': 'taxes_ins',
        'Miscellaneous Expenses': 'misc_exp',
        'Actual Loss': 'actual_loss',
        'Cumulative Modification Costs': 'cum_mod_costs',
        'Interest Rate Step Indicator': 'step_ind',
        'Payment Deferral Flag': 'deferral_flag',
        'Estimated Loan-to-Value (ELTV)': 'eltv',
        'Zero Balance Removal UPB': 'zb_removal_upb',
        'Delinquent Accrued Interest': 'delinq_acc_int',
        'Delinquency Due to Disaster': 'disaster_delinq',
        'Borrower Assistance Plan': 'assist_plan',
        'Current Period Modification Costs': 'mod_cost',
        'Current Interest Bearing UPB': 'int_upb',
        'Mortgage Insurance Cancellation Indicator': 'mi_cancel',
        'Servicer Name': 'servicer',
        'Bankruptcy Cramdown Costs': 'cramdown'
    }
    df = df.rename(columns=mapping)
    
    # Zero Balance Code string mapping
    if 'zb_code' in df.columns:
        df['zb_code'] = df['zb_code'].astype(str).str.zfill(2).replace({'nan': np.nan, '00': np.nan, 'None': np.nan})
        
    return df

def process_vintage(zip_path, schema):
    year = os.path.basename(zip_path).replace('sample_', '').replace('.zip', '')
    logging.info(f"Processing vintage {year} from {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        orig_file = [f for f in zf.namelist() if 'orig' in f][0]
        perf_file = [f for f in zf.namelist() if 'perf' in f][0]
        
        # Read Origination
        with zf.open(orig_file) as f:
            df_orig = pd.read_csv(f, sep='|', header=None, dtype=str, keep_default_na=False, na_values=[''])
            df_orig = map_origination(df_orig, schema)
            
        # Read Performance in chunks (memory efficiency)
        perf_chunks = []
        with zf.open(perf_file) as f:
            for chunk in pd.read_csv(f, sep='|', header=None, dtype=str, keep_default_na=False, na_values=[''], chunksize=500000):
                chunk = map_performance(chunk, schema)
                perf_chunks.append(chunk)
                
        df_perf = pd.concat(perf_chunks, ignore_index=True)
        
    return df_orig, df_perf, year

def derive_canonical_state(status, zb_code):
    # Deriving STATE
    # Freddie Mac mapping:
    # 0 = Current
    # 1 = 30 DPD
    # 2 = 60 DPD
    # ...
    # R = REO
    # XX = Unknown
    # ZB Codes: 01 = Prepaid, 03 = Foreclosure, 09 = REO Disposition, etc.
    
    if pd.notna(zb_code):
        if zb_code == '01': return 'PREPAID'
        elif zb_code in ['02', '03', '09']: return 'DEFAULT' # Third-party sale, foreclosure, REO
        else: return 'OTHER_TERMINAL'
        
    if pd.isna(status) or status == 'XX': return 'UNKNOWN'
    if status == '0' or status == '00': return 'CURRENT'
    if status == '1' or status == '01': return '30_DPD'
    if status == '2' or status == '02': return '60_DPD'
    if status in ['R', 'RA']: return 'DEFAULT' # REO / REO Alternative
    
    # 3+ is 90+ DPD
    try:
        val = int(status)
        if val >= 3:
            return '90_PLUS_DPD'
    except:
        pass
        
    return 'UNKNOWN'

def run_phase1():
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    schema = load_schema()
    zips = glob.glob("data/raw/sample_*.zip")
    
    all_loans = set()
    total_orig = 0
    total_perf = 0
    unmatched_perf = 0
    duplicate_orig = 0
    duplicate_perf = 0
    state_counts = pd.Series(dtype=int)
    terminal_counts = pd.Series(dtype=int)
    
    missing_stats_orig = []
    missing_stats_perf = []
    
    for zip_path in zips:
        df_orig, df_perf, year = process_vintage(zip_path, schema)
        
        # Canonical identifiers
        orig_counts = df_orig['loan_id'].value_counts()
        dups_o = (orig_counts > 1).sum()
        duplicate_orig += dups_o
        
        total_orig += len(df_orig)
        total_perf += len(df_perf)
        all_loans.update(df_orig['loan_id'].unique())
        
        # Check unmatched
        unmatched = ~df_perf['loan_id'].isin(df_orig['loan_id'])
        unmatched_perf += unmatched.sum()
        
        # Duplicate loan-month
        dups_p = df_perf.duplicated(subset=['loan_id', 'period']).sum()
        duplicate_perf += dups_p
        
        # States
        df_perf['canonical_state'] = df_perf.apply(lambda row: derive_canonical_state(row['curr_status'], row.get('zb_code')), axis=1)
        state_counts = state_counts.add(df_perf['canonical_state'].value_counts(), fill_value=0)
        if 'zb_code' in df_perf.columns:
            terminal_counts = terminal_counts.add(df_perf['zb_code'].value_counts(), fill_value=0)
        
        # Missingness
        missing_stats_orig.append(df_orig.isnull().sum())
        missing_stats_perf.append(df_perf.isnull().sum())
        
        # Join static origination to performance to build canonical panel
        # We only keep a subset of static features to save memory
        static_cols = ['loan_id', 'orig_fico', 'orig_ltv', 'orig_dti', 'prop_state', 'prop_type', 'loan_purpose', 'orig_upb', 'orig_interest_rate', 'first_payment_date']
        canonical_panel = pd.merge(df_perf, df_orig[static_cols], on='loan_id', how='left')
        
        # Sort temporally to verify sequence
        canonical_panel = canonical_panel.sort_values(by=['loan_id', 'period'])
        
        # Save chunk
        out_path = f"data/processed/canonical_panel_{year}.parquet"
        canonical_panel.to_parquet(out_path, index=False)
        logging.info(f"Saved {out_path}")
        
    
    # Agg missingness
    agg_miss_orig = pd.DataFrame(missing_stats_orig).sum()
    agg_miss_perf = pd.DataFrame(missing_stats_perf).sum()
    
    # Generate Phase 1 verification report
    report = {
        "vintages_processed": len(zips),
        "unique_loans_origination": len(all_loans),
        "total_monthly_observations": total_perf,
        "duplicate_origination_records": int(duplicate_orig),
        "duplicate_loan_month_records": int(duplicate_perf),
        "monthly_records_without_origination": int(unmatched_perf),
        "state_distribution": state_counts.to_dict(),
        "terminal_event_distribution": terminal_counts.to_dict(),
        "missingness_origination": agg_miss_orig.to_dict(),
        "missingness_performance": agg_miss_perf.to_dict()
    }
    
    with open('reports/phase1_verification.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    logging.info("Phase 1 Ingestion Complete.")
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    run_phase1()
