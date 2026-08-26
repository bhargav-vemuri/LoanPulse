# Critical Limitations & Future Work

No analytical engine is perfect. The Loan Performance Intelligence Engine explicitly operates under the following documented constraints and limitations:

## 1. Missing Official Macro Data
Because the organizer-provided `macro_scenarios.csv` file was unavailable within the development sandbox, the Phase 7 Scenario Engine currently relies on strictly **Project-Defined** micro-perturbations (e.g., FICO Stress, Delinquency Shock). Consequently, the Scenario Sensitivity metrics represent *model-dependent counterfactuals*, not true causal economic forecasts based on GDP or unemployment.

## 2. Missing Servicer Files
Without external Servicer logs or property-specific valuations, the Anomaly Engine operates purely on behavioral statistics derived from the Freddie Mac panel. Future iterations should incorporate NLP embeddings of unstructured servicer notes to determine if a "High Anomaly" transition is actually a documented forbearance agreement.

## 3. Administrative Censoring
Because the dataset terminates in Q4 2025, any snapshot taken after Q4 2024 cannot observe a full 12-month future window. These snapshots are administratively right-censored and must be dropped from the target generation pipeline, slightly reducing the observable volume of the most recent vintage behaviors.

## 4. Competing Risks
While the Phase 5 Survival Intelligence pipeline formally models Prepayments as a competing risk via Aalen-Johansen, the Phase 4 LightGBM supervised models treat prepayments as standard negative outcomes (0) when predicting Default. Advanced multi-task or Fine-Gray hazard models could further unify these endpoints.

## 5. Live LLM Constraints
Because the agentic development sandbox lacked external internet API access to a live GenAI gateway, the Phase 9 Reviewer Intelligence was constructed primarily using the `Deterministic Fallback` templating engine. The application UI explicitly labels this as `Live LLM API: AVAILABLE / NOT VERIFIED`.

## 6. Execution Environment Bug
The development container utilizes Python 3.14.0 (an unstable pre-release). This explicitly breaks the binary `protobuf` dependency required by Streamlit, preventing `app.py` from launching a live web server inside the sandbox. The codebase is structurally sound and must be executed in a standard Python 3.10/3.11 environment.
