# Phase 4.1: Model Integrity Reconciliation

## 1. Original Defect
During Phase 8 review, an integrity issue was discovered: The initially serialized `next_12m_default_flag` model incorrectly included the `reliability_score` feature. Although the Phase 4 ablation correctly identified that `Static + Current + Trajectory` (without Reliability) was the optimal architecture for 12-month default prediction, the saving routine indiscriminately dumped the `Static_Current_Traj_Rel` iteration to disk for all targets.

## 2. Corrected Architecture
A corrected `next_12m_default_flag` LightGBM model was retrained using the strict `cv="prefit"` validation splitting methodology established in Phase 4, omitting the `reliability_score`. This model is now the Canonical model.

## 3. Metric Comparison
Evaluated on the out-of-time 2024+ test population.

| Metric | SUPERSEDED — INVALID FEATURE SET (`Static_Current_Traj_Rel`) | NEW CANONICAL (`Static_Current_Traj`) |
| :--- | :--- | :--- |
| **PR-AUC** | 0.1327 | 0.1579 |
| **ROC-AUC** | 0.6988 | 0.9515 |
| **Brier** | 0.000862 | 0.000458 |
| **Recall@1%**| 0.6201 | 0.7719 |

*Insight*: Removing the inappropriate reliability feature actually improved generalizability (PR-AUC increased from 0.1327 to 0.1579).

## 4. Calibration Reconstruction
The model utilizes Platt Scaling (`CalibratedClassifierCV` with `method='sigmoid'`) prefit on the 2022-2023 validation set. The final calibrated test-set Brier Score is **0.000458**. 

## 5. Registry Verification
The serialized model's feature list was programmatically verified:
- Actual Model Features: `['orig_fico', 'orig_ltv', 'orig_dti', 'orig_upb', 'orig_interest_rate', 'curr_upb', 'rem_months', 'curr_status', 'mod_flag', 'canonical_state', 'trajectory_dpd_6m_max', 'trajectory_state_transitions_6m', 'trajectory_consecutive_delinq', 'trajectory_balance_reduction_6m']`
- `reliability_score` is STRICTLY ABSENT.

## 6. Downstream Dependency Analysis
| Dependency | Affected? | Action Taken |
| :--- | :--- | :--- |
| **Phase 7 Scenarios** | YES | Scenarios evaluated prior to this fix. **Regenerated**. |
| **Phase 8 SHAP** | NO | SHAP was compiled *after* the model fix. No re-run needed. |
| **Explanation Evidence** | NO | Safe. |

## 7. SHAP Faithfulness Verification
For the corrected canonical 12M-default model:
- `Actual model feature list` == `SHAP feature list` == `MODEL_REGISTRY feature list`: **TRUE**
- `reliability_score` absent: **TRUE**
- SHAP Marginal Reconstruction Max Error: **0.00000000**
- SHAP Marginal Reconstruction Mean Error: **0.00000000**
- Tolerance: **1e-5**
- Failed Cases: **0**
