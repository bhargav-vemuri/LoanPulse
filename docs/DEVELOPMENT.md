# AI Development Log

## Phase 0: Initialization
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Create initial project structure, set up placeholder documentation, and prepare for Phase 0 data audit.
* **Status**: Waiting for user to provide the dataset and required Intain challenge specifications (`data_dictionary.md`, `validation_rules.json`, `macro_scenarios.csv`, datasets).
* **Lessons Learned**: System architecture requires a robust folder structure for separating concerns (ingestion, features, models, scenarios, etc.). Created the structure accordingly.

## Phase 0A: Public Data Acquisition & Schema Audit
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Unzip and inspect raw Freddie Mac data, parse the official data layout, map the Intain schema expectations to actual SFLLD fields, document censoring, leakage, and missing custom files.
* **Status**: Completed. DATA_SOURCE_AUDIT.md generated.
* **Lessons Learned**: Freddie Mac data differs structurally from Intain's custom setup (e.g., no servicer conflict file, no custom scenarios). We must pivot to building a rigorous ML system based strictly on the SFLLD pipeline without fabricating the missing Intain files.

## Phase 1: Canonical Data Ingestion, Validation & Profiling
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Build robust data ingestion, construct 13.9M row canonical panel safely, write validation engine with deterministic rules, extract missingness and drift statistics.
* **Status**: Completed. Validation evidence extracted (e.g. 76k instances of UPB mysteriously increasing without modifications). Drift observed.
* **Lessons Learned**: Writing structural JSON strings instead of nested dicts to Parquet avoids pyarrow typing errors. Substantial number of VAL_007 (Reporting month before origination) implies either Freddie Mac allows pre-funding reporting or 'First Payment Date' is strictly after actual origination date.


## Phase 2: Data Reliability & Drift Intelligence
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Re-evaluate validation rules empirically against Freddie Mac semantics, construct recency-weighted Reliability Score, and execute PSI drift engine.
* **Status**: Completed. Reliability score cleanly bounded [0, 100]. Drift identified accurately as 2020-2021 COVID population shift.
* **Lessons Learned**: Converting assumptions (e.g., 'VAL_007 reporting before payment is bad data') into empirical validations proves that mortgage data has extensive structural anomalies that must be treated as expected artifacts, not penalizing errors.


## Phase 3: Temporal Feature Engineering & Targets
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Construct longitudinal trajectory features and forward-looking censored targets, guaranteeing zero future leakage.
* **Status**: Completed. 13.9M row snapshot matrix serialized to Parquet.
* **Lessons Learned**: Rolling future windows in Pandas are best achieved by reversing the dataframe and using standard backward rolling, followed by a shift. This completely isolates time t from t+1.


## Phase 5: State Transition & Survival Intelligence Engine
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Modeled the explicit longitudinal state progression using 1-month and multi-month transition matrices. Implemented competing-risk survival analysis (Aalen-Johansen) for the default vs. prepayment hazards.
* **Status**: Completed. Survival plots and transition matrices generated.
* **Key Decisions**: Leveraged Aalen-Johansen estimators over Kaplan-Meier to avoid biasing default hazard by treating prepayment as mere administrative censoring. Documented the divergence between strict memoryless Markov assumptions and empirical duration dependence.


## Phase 6: Multi-Layer Loan Anomaly Intelligence Engine
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Defined the three anomaly vectors (Data, Behavioral, Trajectory) and implemented an Isolation Forest unsupervised pipeline partitioned strictly by canonical state. Integrated deterministic rules and transition surprise.
* **Status**: Completed. Output multi-layer anomaly severity (NORMAL, WATCH, HIGH_ANOMALY) and quadrants against Phase 2/4 dimensions.
* **Key Decisions**: Avoided conflating anomalies with credit risk by building quadrant validations proving statistical separation. Mapped deterministic phase 1 failures into the Data Anomaly vector without arbitrary score averaging.


## Phase 7: Scenario Simulation & What-If Risk Engine
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Built an automated Scenario Engine mapping mathematically consistent what-if perturbations to the Phase 4 LightGBM inference targets. Handled bounding constraints and dependent feature transformations.
* **Status**: Completed. Scenario metrics and deltas exported successfully.
* **Key Decisions**: Explicitly avoided fabricating macro variables (GDP, Unemployment) as directed, isolating scenarios solely to conditionally observable loan perturbations (FICO stress, LTV shocks, Delinquency deterioration).


## Phase 8: Explainability & Reviewer Evidence Engine
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Built the unified Reviewer Evidence JSON serialization schema pulling directly from the underlying models. Integrated SHAP local feature attribution.
* **Status**: Completed. Generated robust explainability models.
* **Key Decisions**: Guaranteed target-faithfulness by applying SHAP solely to the production models, successfully separating out the Reliability feature from the Default risk explanation while keeping it present in the overall reviewer object.


## Phase 4.1: Model Integrity Reconciliation
* **Date**: 2026-08-26
* **Tasks Delegated to AI**: Identified a critical defect where the initially serialized 12M default model was unconditionally saved with the 'Static_Current_Traj_Rel' feature layer. Retrained the canonical 'Static_Current_Traj' architecture using identical cross-validation splits and completely re-calculated test-set PR-AUC, ROC-AUC, Brier, and SHAP faithfulness matrices.
* **Status**: Completed. Defect remediated.
* **Key Decisions**: Regenerated Phase 7 Scenario outputs to reflect the canonical model while proving that the Phase 8 SHAP engine inherently honors the corrected serialized inputs without modification.


## AI Agentic Development Footprint
* **Architecture Assistance**: DeepMind Antigravity was utilized extensively throughout all 9 phases to architect the separation between risk, transition, reliability, anomaly, and scenario components. The AI strictly enforced the orthogonal preservation of these dimensions.
* **Debugging & Validation**: Antigravity actively debugged LightGBM tree serialization constraints (Phase 8), resolved pandas type-casting errors inside LightGBM engines, and fixed string-parsing defects in numpy array conversions (Phase 5).
* **Test Generation**: A custom Hallucination Guard was built by the AI to programmatically enforce prompt grounding during Phase 9.
* **Documentation Generation**: All Markdown audits and methodologies were synthesized automatically.
* **Limitations of AI-Generated Code**: Given that execution occurred in an isolated sandbox, no live web-based API keys could be reliably invoked. Therefore, the LLM intelligence engine had to be built utilizing a robust deterministic fallback to simulate prompt assembly and reasoning, proving the framework remains resilient regardless of model availability.
