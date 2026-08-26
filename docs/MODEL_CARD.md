# Model Card

## Intended Use
The Loan Performance Intelligence Engine provides decision support to human risk reviewers by disentangling true credit risk, data reliability, behavioral anomalies, and counterfactual sensitivity. It is not intended for fully automated lending decisions.

## Data
- **Source**: Freddie Mac Single Family Loan-Level Dataset (SFLLD).
- **Scale**: 400,000 unique loans, 13,899,867 monthly observations.
- **Coverage**: Vintages 2018–2025.

## Temporal Split
- **Train**: 201802 – 202112
- **Validation (Calibration)**: 202201 – 202312
- **Out-of-Time Test**: 202401+

## Targets
- `next_3m_delinquency_flag`
- `next_6m_delinquency_flag`
- `next_12m_default_flag`
- `next_12m_prepayment_flag`

## Models
- **Algorithm**: `LightGBM` (Gradient Boosting Machines).
- **Class Imbalance**: Handled natively via `scale_pos_weight`.
- **Calibration**: Platt Scaling (Sigmoid) on the validation set.

## Features
The canonical feature layers are:
- **Static**: Origination FICO, UPB, DTI, LTV, Interest Rate.
- **Current**: Current DPD status, current UPB, remaining months.
- **Trajectory**: 6-month historical vectors (e.g., max DPD, consecutive delinquency, state transitions, balance reduction).
- **Reliability**: Deterministic rules-engine outputs mapping evidence quality.

**CRITICAL FEATURE ABLATION NOTE:**
- The **12M Default Model** uses: `Static + Current + Trajectory`. It **DOES NOT** use Reliability.
- Other models (3M/6M delinquency, 12M prepayment) may use `Reliability` as an orthogonal feature mapping.

## Out-of-Time Evaluation (12M Default)
- **PR-AUC**: 0.1579 (Highly robust given ~0.04% baseline prevalence)
- **ROC-AUC**: 0.9515
- **Brier Score**: 0.000458

## Limitations & Known Risks
- The models were trained without external Servicer data or official Intain macroeconomic scenarios.
- The 12-month default target suffers from administrative right-censoring in the Q4 2025 tail of the panel.
