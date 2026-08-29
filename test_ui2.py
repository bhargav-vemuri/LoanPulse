import sys
import pandas as pd
from app import load_data

df = load_data()
demo_cases = ['F23Q40107321', 'F23Q40094248', 'F22Q20274635', 'F22Q30281245', 'F22Q20387625', 'F21Q40212345']
for loan_id in demo_cases:
    case = df[df['loan_id'] == loan_id]
    if case.empty:
        print(f'Demo case {loan_id} not found! (Normal if out-of-sample)')
    else:
        print(f'Demo case {loan_id} exists. Row retrieved.')
print('ALL DEMO CASES QUERIED.')
