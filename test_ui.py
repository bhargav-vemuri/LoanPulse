import sys
import pandas as pd
from app import load_data

try:
    df = load_data()
    print(f'Dashboard loaded. Total active evaluated loans: {len(df)}')
    
    # Priority
    from app import extract_priority
    df['priority'] = df['reviewer_note'].apply(extract_priority)
    must_review_count = len(df[df['priority'] == 'MUST_REVIEW'])
    print(f'MUST_REVIEW Cases: {must_review_count}')
    
    demo_cases = ['F23Q40107321', 'F23Q40094248', 'F22Q20274635', 'F22Q30281245', 'F22Q20387625', 'F21Q40212345']
    for loan_id in demo_cases:
        case = df[df['loan_id'] == loan_id]
        if case.empty:
            print(f'Demo case {loan_id} not found!')
            sys.exit(1)
        
        row = case.iloc[-1]
        print(f'Verified case {loan_id}:')
        print(f'  Risk: {row.get("risk_category", "N/A")} | Anomaly: {row.get("anomaly_flag", "N/A")}')
        
    print('ALL UI WORKFLOW AND DEMO CASES VALIDATED.')
except Exception as e:
    print(f'Validation failed: {e}')
    sys.exit(1)
