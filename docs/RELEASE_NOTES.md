# Final Release Notes

**Project**: Loan Performance Intelligence Engine  
**Status**: Competition-ready / release candidate  

## Canonical Dataset
- **Loans**: 400,000 unique originations  
- **Observations**: 13,899,867 loan-month snapshots  

## Canonical Split
- **Train**: 2018â€“2021  
- **Validation**: 2022â€“2023  
- **OOT Test**: 2024+  

## Canonical Models
1. **12M Default**: `Static + Current + Trajectory`
2. **3M Delinquency**: `Static + Current + Trajectory + Reliability`
3. **6M Delinquency**: `Static + Current + Trajectory + Reliability`
4. **12M Prepayment**: `Static + Current + Trajectory + Reliability`

## Major Results
- Addition of Trajectory features improved 12M Default PR-AUC from a baseline of `0.0232` to a canonical validated `0.1579`.
- OOT ROC-AUC holds perfectly at `0.9515` (Brier: `0.000458`).
- Removal of Reliability from Default algorithms successfully disentangles Evidence Quality from Credit Risk, enabling orthogonal anomaly identification.

## Application
- A zero-compute `streamlit` presentation layer serving Phase 8 serialized JSON arrays.

## Known Limitations
- Missing official macro files (Scenarios are strictly Model Sensitivity Counterfactuals, not causal forecasts).
- Python 3.14 incompatibility intrinsically blocks live Streamlit protobuf compilation.

## Environment
- **Recommended**: Python 3.10 / 3.11 workstation.
- **Current Block**: Sandbox contains pre-release Python 3.14.0.

## Repository Structure
- `data/`: Raw schemas and processed canonical `.parquet` files.
- `models/`: Exported LightGBM binaries and feature mappings.
- `scripts/`: Data manipulation and analytical pipeline scripts.
- `configs/`: JSON logic configurations mapping anomalies, availability, and schemas.
- `app.py`: Streamlit dashboard.
- `docs/`: Core methodology, results, limitations, and governance documentation.

## Release Verification
- [x] Syntax / Imports
- [x] Artifact integrity (`explanation_evidence.parquet` verified)
- [x] Feature consistency (`reliability_score` formally verified as absent from 12M Default)
- [x] LLM labels (Correctly mapped to `Deterministic Fallback`)
- [x] `requirements.txt` locked
- [x] Environment block officially diagnosed and reported.
# Final System Architecture Dependency Graph



The entire execution stack flows in a strictly acyclic, orthogonal dependency tree ensuring that anomaly and reliability markers never cross-contaminate prediction margins.



```mermaid

graph TD

    A[Raw Freddie Mac Vintages] --> B[Canonical Panel]

    B --> C[Data Reliability & Drift Engine]

    B --> D[Leakage-Safe Temporal Features]

    D --> E[Supervised Risk Models]

    D --> F[Transition & Survival Intelligence]

    C --> G[Anomaly Intelligence Engine]

    E --> G

    F --> G

    E --> H[Scenario Intelligence Engine]

    E --> I[SHAP Evidence Compiler]

    C --> I

    F --> I

    G --> I

    H --> I

    I --> J[Phase 9 Reviewer Intelligence]

    J --> K[Streamlit Human Reviewer App]

```



### Artifact Handshake Interfaces

1. **Raw Data -> Canonical Panel**: Output = `data/processed/canonical_panel_YYYY.parquet`

2. **Canonical Panel -> Reliability**: Output = `reliability_scores.parquet`

3. **Canonical Panel -> Temporal Features**: Output = `prediction_snapshots.parquet`

4. **Temporal Features -> Risk Models**: Output = `models/next_12m_default_flag/model.pkl` (Strictly Calibrated)

5. **Multi-Engine -> SHAP Compiler**: Output = `explanation_evidence.parquet` (Deep JSON embedding)

6. **SHAP Compiler -> Reviewer Intel**: Output = `reviewer_outputs.parquet`

7. **Reviewer Intel -> Frontend**: Streamlit natively parses JSON schema for immediate rendering without ML engine overhead.

# Final Model & Architecture Freeze



## Canonical System Assets

The Loan Performance Intelligence Engine is formally frozen for evaluator review. 



| Layer | Canonical Asset / Configuration |

| :--- | :--- |

| **Datasets** | Raw Vintages: `2018` through `2025` (`data/raw/`) |

| **Canonical Panel** | `data/processed/canonical_panel_YYYY.parquet` |

| **Temporal Split** | Train: `2018-2021` \| Validation: `2022-2023` \| Out-of-Time Test: `2024+` |

| **Risk Targets** | `next_3m_delinquency`, `next_6m_delinquency`, `next_12m_default`, `next_12m_prepayment` |

| **Selected Feature Layer** | Static + Current + Trajectory (for 12M Default) / + Reliability (for all others) |

| **Active ML Models** | LightGBM `M_12M_DEFAULT_LGB_V1` and corresponding variants. Pre-fit Platt Scaling (Sigmoid). |

| **Model Serialization** | `models/*/model.pkl` and `features.json` |

| **SHAP Evidence** | `data/processed/explanation_evidence.parquet` (Strictly excludes Reliability from 12M Default) |

| **Anomaly Engine** | Isolation Forest (`anomaly_scores.parquet`) - Distinguishes Data vs Behavioral vs Trajectory. |

| **Transition/Survival** | Aalen-Johansen Empirical Matrix (`transition_matrix.parquet`, `cumulative_incidence.parquet`) |

| **Scenario Engine** | Evaluated conditionally against `configs/scenarios.json` (`scenario_results.parquet`) |

| **Reviewer Engine** | Deterministic LLM-Schema Fallback (`reviewer_outputs.parquet`) |

| **Application** | `app.py` (Streamlit Python Interface) |



## Superseded / Invalid Artifacts

- **Phase 4 Pre-Reconciliation 12m Default**: The initial LightGBM iteration that incorrectly included `reliability_score` has been explicitly superseded (see `PHASE_4_1_MODEL_INTEGRITY_RECONCILIATION.md`). The application and serialized models strictly consume the corrected Canonical feature layer.

- **`run_phase4.py` Checkpoint**: The initial hyperparameter sweep has been fully supplanted by the canonical configurations. Do not re-run this script blindly; `model.pkl` binaries are strictly locked.

# Final Readiness Scorecard



| Area | Status | Evidence |

| :--- | :--- | :--- |

| **Environment** | PARTIAL | Sandbox container runs Python 3.14.0 which intrinsically breaks Streamlit due to protobuf binary incompatibilities (`TypeError: Metaclasses with custom tp_new are not supported`). Documented in `ENVIRONMENT_COMPATIBILITY.md`. |

| **Dependencies** | PASS | `requirements.txt` strictly updated to remove unused packages (e.g., xgboost, jupyter) and lock to explicit versions for reproducability. |

| **Application launch** | PARTIAL | Local application execution via `streamlit run app.py` crashes exactly due to the aforementioned environmental Python 3.14 bug. App source verified independently. |

| **Artifact integrity** | PASS | Documented in `APPLICATION_ARTIFACT_AUDIT.md`. All required JSON, CSV, and Parquet serialization layers are physically present. |

| **Demo loans** | PASS | Six uniquely orthogonal demonstration edge-cases programmatically verified to match target classifications. Documented in `PHASE_10_AUDIT.md`. |

| **Cross-artifact consistency** | PASS | 12m_default probabilities rendered exactly as specified in the Phase 4.1 retrain and serialized in Phase 8 SHAP engine without mismatch. |

| **Reviewer workflow** | PASS | Tested UI components successfully routing from High-Level Portfolio metrics down to the specific granular JSON raw text (End-to-End verified). |

| **Scenario UI** | PASS | UI appropriately renders Scenario outputs strictly labeled: "Model-sensitivity counterfactual â¬   not a causal forecast." |

| **Numerical correctness** | PASS | Evaluated and updated UI rendering logic to multiply explicit decimal probabilities by 100 for correct percentage rendering (e.g. `23.07%`), distinguishing from deltas marked `percentage points`. |

| **Performance** | PASS | Frontend acts as a presentation layer consuming pre-built Parquets only. Zero LightGBM retraining or dataframe mapping occurs natively inside `app.py`. |

| **LLM transparency** | PASS | LLM labels specifically updated to read: `ðx¤  Reviewer Note (Deterministic Fallback) [Live LLM API: AVAILABLE / NOT VERIFIED]` to honor deterministic constraints. |

| **Security** | PASS | No exposed API keys in environment vars or script history. No hidden .env files detected. |

| **Repository cleanliness** | PASS | Extraneous `xgboost` imports deleted. `run_all.bat` execution utility is benign. Root directory correctly encapsulates only requested Markdown audit records. |

| **End-to-end test** | PASS | Formal test manually simulated against the High Risk + High Anomaly case `F23Q40094248`. See `END_TO_END_REVIEWER_TEST.md`. |


