# Consolidated Methodology

## State Definition

# Canonical State Definition

The `canonical_state` field represents the status of a loan in a given reporting month. It is derived primarily from the Freddie Mac `Current Loan Delinquency Status` and `Zero Balance Code` fields.

## State Derivation Logic

The priority of derivation follows Terminal Events first, then Delinquency Status.

1. **Terminal States (Derived from `Zero Balance Code`)**
   - **PREPAID**: `Zero Balance Code` == '01' (Prepaid or Matured). The loan has been fully paid off.
   - **DEFAULT**: `Zero Balance Code` IN ('02', '03', '09'). Third-party sale, Foreclosure, or REO Disposition. The loan was terminated with a credit event.
   - **OTHER_TERMINAL**: Any other populated `Zero Balance Code` (e.g., '06' Repurchased).

2. **Active States (Derived from `Current Loan Delinquency Status`)**
   - **CURRENT**: `Status` == '0' or '00'. The loan is current or less than 30 days past due.
   - **30_DPD**: `Status` == '1' or '01'. The loan is 30-59 days past due.
   - **60_DPD**: `Status` == '2' or '02'. The loan is 60-89 days past due.
   - **90_PLUS_DPD**: `Status` numeric value >= 3. The loan is 90 or more days past due.
   - **DEFAULT**: `Status` IN ('R', 'RA'). The property is in REO or REO Alternative.
   - **UNKNOWN**: `Status` == 'XX' or is missing.


## Data Lineage

# Data Lineage

This document traces the origin of normalized fields in the LoanPulse Canonical Data Panel back to the raw Freddie Mac Single-Family Loan-Level Dataset (SFLLD).

## Identifiers & Temporal Keys
* **loan_id**: Freddie Mac `Loan Identifier` (Alpha Numeric - PYYQnXXXXXXX). Present in both Origination and Performance.
* **period**: Freddie Mac `Period` (YYYYMM). The reporting month.
* **first_payment_date**: Freddie Mac `First Payment Date` (YYYYMM).

## Static Origination Features
* **orig_fico**: Freddie Mac `Classic FICO®`. Numeric score. Nullified if '9999'.
* **orig_ltv**: Freddie Mac `Original Loan-to-Value (LTV)`. Nullified if '999'.
* **orig_dti**: Freddie Mac `Original Debt-to-Income (DTI) Ratio`. Nullified if '999'.
* **orig_upb**: Freddie Mac `Original UPB`.
* **orig_interest_rate**: Freddie Mac `Original Interest Rate`.
* **prop_state**: Freddie Mac `Property State`.
* **prop_type**: Freddie Mac `Property Type`.
* **loan_purpose**: Freddie Mac `Loan Purpose`.

## Monthly Performance Features
* **curr_upb**: Freddie Mac `Current Actual UPB`.
* **curr_status**: Freddie Mac `Current Loan Delinquency Status`.
* **rem_months**: Freddie Mac `Remaining Months to Legal Maturity`.
* **mod_flag**: Freddie Mac `Modification Flag`.
* **zb_code**: Freddie Mac `Zero Balance Code`. Zero-padded to 2 digits.

## Derived Variables
* **canonical_state**: Derived computationally from `Current Loan Delinquency Status` and `Zero Balance Code` (See `STATE_DEFINITION.md`).


## Reliability Methodology

# Data Reliability Methodology

The Data Reliability Score (0-100) measures how trustworthy the empirical evidence supporting a loan is. It explicitly does **NOT** measure predictive default risk or borrower creditworthiness.

## Core Design Principles
1. **Evidence-Based Penalities**: A loan begins with a score of 100. Points are deducted based on observed data anomalies across the longitudinal panel.
2. **Recency Awareness**: Validation violations observed recently (within the last 12 months) carry full weight. Violations further in the past carry a 0.5x decay weight, reflecting that older data inconsistencies are less likely to corrupt current predictions.
3. **Risk Independence**: The score is not trained against prediction targets. It remains an independent confidence signal.

## Scoring Components
The taxonomy maps each `rule_id` to a severity class and a base penalty:

| Category | Rule ID | Classification | Base Penalty | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **TEMPORAL_INTEGRITY** | VAL_001 | HARD_ERROR | -15 | Negative maturity months. |
| **BALANCE_CONSISTENCY** | VAL_002 | SOFT_WARNING | -5 | UPB exceeding original UPB without explicit modification. |
| **ATTRIBUTE_COMPLETENESS** | VAL_003 | INFORMATIONAL | -2 | Missing FICO. |
| **ATTRIBUTE_COMPLETENESS** | VAL_004 | HARD_ERROR | -10 | Missing Original LTV. |
| **STATE_CONSISTENCY** | VAL_005 | HARD_ERROR | -20 | Terminal Zero-Balance code with positive UPB. |
| **TRAJECTORY_INTEGRITY** | VAL_006 | DATA_QUALITY_SIGNAL | -10 | Inconsistent delinquency gap (e.g. Current to 60 DPD directly). |
| **REPORTING_CONVENTION** | VAL_007 | STRUCTURAL_EXPECTED | 0 | Observation precedes first scheduled payment. |
| **STATE_CONSISTENCY** | VAL_008 | HARD_ERROR | -20 | Zombie observations reported after a terminal event. |

## Reliability Bands
* **HIGH**: 90 - 100
* **MEDIUM**: 70 - 89
* **LOW**: < 70


## Target Definitions

# Target Definitions

This document details the precise derivation logic for all supervised prediction targets.

### 1. `next_3m_delinquency_flag`
* **Definition**: Will the loan experience a state of 30+ Days Past Due (DPD) or worse within the next 3 months?
* **Source Fields**: `canonical_state`
* **Future Window**: `[t+1, t+3]`
* **Event**: `canonical_state` IN (`30_DPD`, `60_DPD`, `90_PLUS_DPD`, `DEFAULT`) during the window.
* **Eligibility & Censoring**: A snapshot is eligible if (a) the event occurs, OR (b) we observe all 3 subsequent months without the event.

### 2. `next_6m_delinquency_flag`
* **Definition**: Will the loan experience a state of 30+ DPD or worse within the next 6 months?
* **Future Window**: `[t+1, t+6]`
* **Event**: Same as above.
* **Eligibility & Censoring**: Eligible if event occurs OR full 6 months observed.

### 3. `next_12m_default_flag`
* **Definition**: Will the loan experience a terminal default event within the next 12 months?
* **Source Fields**: `canonical_state`
* **Future Window**: `[t+1, t+12]`
* **Event**: `canonical_state` == `DEFAULT`.
* **Eligibility & Censoring**: Eligible if event occurs OR full 12 months observed without event. 

### 4. `next_12m_prepayment_flag`
* **Definition**: Will the loan prepay in full within the next 12 months?
* **Source Fields**: `canonical_state`
* **Future Window**: `[t+1, t+12]`
* **Event**: `canonical_state` == `PREPAID`.
* **Eligibility & Censoring**: Eligible if event occurs OR full 12 months observed without event. Note: Prepayment and Default are competing risks.

### 5. `next_state`
* **Definition**: The exact canonical state of the loan at month `t+1`.
* **Future Window**: Exactly `t+1`.
* **Eligibility & Censoring**: Eligible if a record for `t+1` exists.

## Missing Future Months (Gap Handling)
If a loan history is missing month `t+1` but reappears in `t+2`, the target logic ignores the gap and checks the available months within the window. If the loan terminates (e.g. prepaid) at `t+2`, `t+3` is naturally missing (expected termination) and counts as having fully observed the loan's terminal state for the 12-month window.

## Competing Risks & Censoring Addendum
Following the Phase 3 Audit, we confirmed that terminal states (Prepayment, Default, Other Terminal) act as absolute absorbing boundaries. A loan that prepays within a 12-month future window is explicitly classified as a **negative event** (0) for default, not an administratively censored event (NaN). Administrative censoring is strictly reserved for dataset truncation (e.g., reaching the end of the available panel without a terminal event).


## Prediction Timestamp Definition

# Prediction Timestamp Definition

## The Modeling Unit
The fundamental unit of observation and prediction is **`loan_id` × `prediction_month` (t)**. 

Each row in the final modeling matrix represents a distinct prediction opportunity for a specific loan at a specific point in time.

## Information Available at Time t
A feature is strictly considered available at time `t` if and only if it represents an attribute whose state is definitively known at or before the close of `prediction_month`.
* **Static Attributes**: `orig_fico`, `orig_ltv`, `orig_dti`, etc. known permanently from origination.
* **Contemporaneous State**: `curr_upb`, `canonical_state`, `curr_status` for month `t`.
* **Historical Trajectory**: Any derived rolling window metric (e.g. max DPD) calculated exclusively over months `[t-k, ..., t]`.

## Excluded Information (Leakage Prevention)
Any field representing a status or event occurring at `t+1` or beyond is strictly classified as **FUTURE_LEAKAGE** and cannot be used as a feature. This includes `Zero Balance Code` (if it represents a terminal event in a future month), actual loss amounts, and future modification flags.

## Target Alignment
All targets represent events that occur in the forward-looking window `[t+1, t+k]`. 
Month `t` is NEVER included in the target evaluation. If a loan is already in default at month `t`, it may be excluded from default prediction depending on the modeling strategy, but it cannot trigger a positive `next_12m_default_flag` based on its state at `t`.


## Transition Survival Methodology

# Transition & Survival Methodology

- **State Space:** 7 explicit states defined by `STATE_DEFINITION.md`.
- **Absorbing States:** DEFAULT, PREPAID, OTHER_TERMINAL. These states enforce P(X->X) = 1.0.
- **Right-Censoring:** Administrative censoring (dataset termination) is explicitly mapped to E=0. No fabricated transitions occur.
- **Comparison to Phase 4:** Phase 4 answers 'Will it default in exactly 12 months?' using supervised ML. Phase 5 answers 'How does the hazard evolve month-over-month?' providing a longitudinal trajectory.

## Default Absorbing-State Documentation
For the canonical one-month transition engine, DEFAULT, PREPAID, and OTHER_TERMINAL are intentionally treated as absorbing states (enforcing P(X->X) = 1.0). This is an abstraction necessary to ensure that the theoretical Markov chains converge cleanly for short-horizon comparative modeling without looping indefinitely or requiring complex termination boundaries.

However, the empirical 12-month matrix compares the state at month t directly against the state at month t+12. Under this empirical endpoint classification, a loan that is DEFAULT at month t may actually be resolved into an REO or alternative liquidation state prior to t+12. Therefore, the empirical matrix naturally exhibits transitions such as DEFAULT -> OTHER_TERMINAL. This reflects actual endpoint resolution across a 12-month span, whereas the one-month matrix abstracts these terminal-to-terminal reclassifications to maintain a stable, non-cyclical active state space.


## Anomaly Methodology

# Anomaly Methodology

## 1. Deterministic Integration
Data anomalies are inherited directly from `validation_evidence.parquet`. A loan-month observation that triggered any critical validation rule in Phase 1 is immediately flagged as a Data Anomaly.

## 2. Transition Surprise
Using the Phase 5 empirical transition matrix, we compute the transition probability $p = P(S_t | S_{t-1})$.
The Transition Anomaly Score is defined as $-\log(p)$.
* If $p < 0.005$ (0.5%), the transition is extremely rare -> flagged as `HIGH_ANOMALY`.
* If $p < 0.02$ (2%), the transition is uncommon -> flagged as `WATCH`.
Transitions with $p=0$ (impossible under canonical mapping) are maximally penalized.

## 3. Peer-Relative Statistical Model
We employ an `IsolationForest` to detect Behavioral and Trajectory anomalies.
* **Peer Grouping**: Models are fit strictly partitioned by `canonical_state`. Delinquent loans are compared to delinquent loans; current loans to current loans.
* **Features Used**: `curr_upb`, `curr_interest_rate`, `trajectory_balance_reduction_6m`, `trajectory_consecutive_delinq`.
* **Classification**: The Isolation Forest outputs an anomaly score (lower is more anomalous). We threshold the lowest 1% as `HIGH_ANOMALY` and the next 4% as `WATCH`.

## 4. Multi-Layer Anomaly Score
The components are aggregated using a strict hierarchy, not an arbitrary average.
An observation is `HIGH_ANOMALY` if it is a Data Anomaly, has a top 1% Statistical Outlier score, OR has a Transition Surprise $p < 0.005$.
An observation is `WATCH` if it avoids `HIGH_ANOMALY` but has a top 5% Statistical Outlier score OR Transition Surprise $p < 0.02$.

## 5. Separation from Risk & Reliability
The anomaly engine is completely unsupervised and unaware of `next_12m_default_flag` (Risk) or Phase 2 `reliability_score` (Reliability). Quadrant analysis empirically demonstrates that High Risk $\neq$ High Anomaly.


## Scenario Methodology

# Scenario Methodology
    
The Scenario Simulation & What-If Risk Engine evaluates conditional risk sensitivity by applying isolated, mathematically bounded perturbations to individual loan observations.

### Macroeconomic Philosophy
* **NO FABRICATED MACRO SCENARIOS**: The organizer-provided `macro_scenarios.csv` was not available in the dataset.
* Therefore, no official Intain macroeconomic assumptions (e.g., GDP, housing prices) are fabricated.
* All scenarios are strictly `PROJECT_DEFINED` loan-level perturbations.
* Scenario results represent **conditional model sensitivity** (i.e. "What if this specific loan's FICO dropped by 50 points?"), NOT top-down economic forecasts.

### Consistency Enforcement
Every scenario enforces dependent-variable consistency to prevent impossible counterfactuals. For example, shocking a loan from `CURRENT` to `30_DPD` simultaneously updates `curr_status`, `canonical_state`, `trajectory_consecutive_delinq`, and `trajectory_dpd_6m_max`.


## Explainability Methodology

# Explainability Methodology

The Phase 8 Reviewer Evidence Engine aggregates deterministic logic, probabilistic surprises, unsupervised anomaly detection, and conditional sensitivity into a unified, traceable evidence chain. 

## Evidence Hierarchy
1. **Model Prediction**: The calibrated forward-looking risk probabilities produced by the Phase 4 LightGBM estimators.
2. **Feature Contributions**: Local feature-attribution utilizing TreeSHAP. SHAP values quantitatively identify which specific observable factors pushed the model's prediction higher or lower relative to the population baseline.
3. **Trajectory Evidence**: A reconstructed 6-month historical array of the loan's state progression, highlighting consecutive delinquency streaks, maximum recent DPD, and balance trajectories.
4. **Transition Evidence**: Evaluating the empirical novelty of the most recent month-to-month state transition based on the Phase 5 matrix.
5. **Reliability Evidence**: Incorporating the deterministic validation flags and the Phase 2 Reliability Score. **Importantly, low reliability implies reduced confidence in the underlying data, NOT inherently higher credit risk.**
6. **Anomaly Evidence**: Distinguishing between Data Anomalies (deterministic), Behavioral Anomalies (unsupervised peer-relative deviations), and Trajectory Anomalies. 
7. **Scenario Sensitivity**: Project-defined what-if stress tests (e.g. FICO shocks) assessing the loan's conditional risk trajectory.
8. **Reviewer Summary**: A prioritized classification scheme highlighting mathematically contradictory or extreme edge cases for manual review.

## Feature Semantic Grouping
Raw predictive features are aggregated into human-interpretable categories:
* **Static borrower/origination**: `orig_fico`, `orig_ltv`, `orig_dti`, `orig_upb`, `orig_interest_rate`
* **Current condition**: `curr_status`, `canonical_state`, `curr_upb`, `rem_months`, `mod_flag`
* **Trajectory**: `trajectory_dpd_6m_max`, `trajectory_consecutive_delinq`, `trajectory_state_transitions_6m`, `trajectory_balance_reduction_6m`
* **Reliability**: `reliability_score` (Note: Strictly excluded from 12M Default explanations).


## Llm Reviewer Methodology

# LLM Reviewer Methodology

The Phase 9 LLM-Assisted Reviewer Intelligence layer is designed strictly as a communication, synthesis, and retrieval interface. It is architecturally prohibited from functioning as a hidden predictive model.

## 1. Evidence-First Architecture
The LLM does NOT ingest the raw dataset. Its sole input is the `explanation_evidence.parquet` object generated in Phase 8.
**Architecture Flow**:
`Loan snapshot -> Phase 2-8 analytical engines -> explanation_evidence -> LLM Prompt -> Reviewer Note -> Hallucination Guard`

## 2. LLM Responsibilities & Prohibitions
**Responsibilities**:
- Summarize structured JSON evidence into a unified reviewer narrative.
- Preserve orthogonal contradictions (e.g., High Risk vs. High Reliability).
- Generate grounded reviewer questions.
- Assign Reviewer Priority (ROUTINE, WATCH, MUST_REVIEW) based solely on provided evidence.

**Prohibitions**:
- The LLM MUST NOT calculate probabilities.
- The LLM MUST NOT invent missing data or macroeconomic assumptions.
- The LLM MUST NOT alter anomaly classifications or reliability scores.

## 3. Strict Grounding & Hallucination Guard
To enforce compliance, the pipeline utilizes a **Hallucination Guard**.
Every generated note is post-processed via `validate_grounding(evidence_json, reviewer_note)`. The guard guarantees that:
- The predicted probability string is explicitly present in the text.
- The canonical trajectory states are represented accurately.
- The anomaly severity and reliability band are verbatim.
If the LLM hallucinates unsupported numerical data or contradictions, the output is flagged `INVALID` and rejected.

## 4. Deterministic Fallback
In environments where live LLM API access is interrupted or disabled, the pipeline automatically routes to a **Deterministic Fallback Engine**. This ensures the analytical system remains fully functional without relying on external generative models, proving the LLM is strictly an assistance layer.

## 5. Prioritization Framework
Priority is deterministically categorized rather than relying on an arbitrary numeric sum:
- **MUST_REVIEW**: Observations where high risk intersects with poor evidence quality (Low Reliability) or unprecedented pathways (High Anomaly), or where low risk contradicts a High Anomaly state.
- **WATCH**: Any observation flagged as High Risk or High Anomaly independently.
- **ROUTINE**: Expected, low-risk behavior operating under normal evidence conditions.


