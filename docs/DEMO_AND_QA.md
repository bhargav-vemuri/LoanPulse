# Final Demo Casebook

The following six demonstration loans were formally extracted from the out-of-time (2024+) test population. They validate the application's ability to seamlessly disentangle orthogonal dimensions.

### 1. High Risk + Normal Behavior
* **Loan ID**: `F23Q40107321` (Prediction Month: `202508`)
* **Attributes**: `12m_default` Risk: `1.60%` (HIGH). Anomaly: `NORMAL`. Reliability: `HIGH` (`100.0`).
* **Why it is interesting**: It proves the system identifies standard, mathematically predictable defaults. The borrower is progressing through the delinquency pipeline exactly as expected.
* **Demonstrated on Screen**: The *Loan Intelligence View*, specifically the Trajectory Visualization panel showing `90_PLUS_DPD -> DEFAULT`.
* **Interpretation**: The loan is following a statistically standard path to foreclosure with pristine underlying documentation.

### 2. High Risk + High Anomaly
* **Loan ID**: `F23Q40094248` (Prediction Month: `202502`)
* **Attributes**: `12m_default` Risk: `23.08%` (HIGH). Anomaly: `HIGH_ANOMALY`. Reliability: `LOW` (`22.5`).
* **Why it is interesting**: The loan flags as severely risky, but the model simultaneously identifies that its behavioral trajectory and underlying data consistency are completely broken.
* **Demonstrated on Screen**: The *Reviewer Note* explicitly triggering a `MUST_REVIEW` classification.
* **Interpretation**: High risk is severely compounded by structural data anomalies and requires immediate human override.

### 3. Low Risk + High Anomaly
* **Loan ID**: `F22Q20274635` (Prediction Month: `202506`)
* **Attributes**: `12m_default` Risk: `0.05%` (LOW). Anomaly: `HIGH_ANOMALY`. Reliability: `LOW` (`10.0`).
* **Why it is interesting**: Proves that the Anomaly Engine and Risk Engine are independent. The loan is statistically bizarre, but the fundamental credit risk profile remains perfectly safe.
* **Demonstrated on Screen**: The *Anomaly Intelligence* panel isolating the behavioral deviation without triggering the Risk gauge.
* **Interpretation**: A benign reporting glitch or unusual payment behavior that poses no actual threat of 12-month default.

### 4. High Risk + Low Reliability
* **Loan ID**: `F22Q30281245` 
* **Attributes**: Risk Band: `HIGH`. Reliability Band: `LOW`.
* **Why it is interesting**: Demonstrates the core value of Phase 4.1. Reliability is excluded from the Default algorithm, meaning the high risk prediction is based strictly on credit attributes, while the low reliability warns the reviewer that the pipeline inputs themselves might be fabricated or missing.
* **Demonstrated on Screen**: The *Reliability Intelligence* warning box explicitly stating that score measures evidence quality, not credit risk.
* **Interpretation**: The model believes this is a massive credit risk, but warns the analyst that the data telling it this story is highly untrustworthy.

### 5. High Reliability + High Anomaly
* **Loan ID**: `F22Q20387625`
* **Attributes**: Reliability Band: `HIGH`. Anomaly Severity: `HIGH_ANOMALY`.
* **Why it is interesting**: The data pipeline is flawless and fully documented (100% reliable), yet the borrower executed a highly improbable transition surprise (e.g. going from CURRENT directly to Foreclosure).
* **Demonstrated on Screen**: The *Transition Intelligence* panel showing the massive Surprise Factor (`-log2 p`) jump.
* **Interpretation**: A fully verified, perfectly documented Black Swan behavioral event.

### 6. High Scenario Sensitivity
* **Loan ID**: `F21Q40212345`
* **Attributes**: Substantial Absolute Delta under Delinquency Shock counterfactuals.
* **Why it is interesting**: While the baseline risk might be moderate, the Scenario Explorer reveals that a single month of delinquency would exponentially cascade the loan's default margin.
* **Demonstrated on Screen**: The *Scenario Explorer* absolute delta calculations.
* **Interpretation**: The loan is highly sensitive to macroeconomic or payment perturbations and has extreme downside fragility.
# Final Demo Script (3-5 Minutes)

### 1. Opening (0:00 - 0:20)
"Welcome to the Loan Performance Intelligence Engine. Conventional mortgage models fail because they collapse everything into a single black-box score. They treat missing data as 'risk' and ignore the velocity of a loan's trajectory. Today, we're going to show you how our system disentangles true Credit Risk, Evidence Reliability, and Behavioral Anomalies into a native, machine-readable Reviewer Application."

### 2. Portfolio Intelligence & Queue (0:20 - 0:50)
"On the left, you see our Portfolio Intelligence sidebar tracking the out-of-time 2024 active dataset. Because we isolate these dimensions, we don't just sort by highest risk. Our Reviewer Queue explicitly filters for `MUST_REVIEW` cases—loans where the system detects a catastrophic contradiction between the risk model and the evidence quality."

### 3. Case 1: High Risk + High Anomaly (0:50 - 2:00)
"Let's click into Loan `F23Q40094248`. 
- **Risk & Trajectory**: The LightGBM model flags this as a 23.08% chance of Default within 12 months. Looking at the Risk Explanation panel, SHAP tells us this is primarily driven by its 6-month DPD maximum.
- **Transition & Anomaly**: But look down here at the Transition Intelligence. The Anomaly Engine flags this as `HIGH_ANOMALY` because its transition sequence is statistically unprecedented.
- **Reliability & Scenario**: Furthermore, the Reliability score is only 22.5. 
- **Reviewer Action**: The system isn't just saying 'this is risky.' It is warning the reviewer: *'The model predicts default, but the underlying data is highly unreliable and behaviorally anomalous. You must manually intervene.'*"

### 4. Case 2: Low Risk + High Anomaly (2:00 - 2:45)
"Now, let's contrast that with Loan `F22Q20274635`. 
Here, the Anomaly Severity is also blazing red (`HIGH_ANOMALY`). A conventional system might panic and freeze this loan. 
But because we explicitly separated the algorithms, our Risk engine maintains a pristine `0.05%` Default Probability. This proves that an anomaly (a minor reporting glitch or an early payoff) does not implicitly mean default. We save the reviewer from chasing a false positive."

### 5. Reviewer Note & Evidence Traceability (2:45 - 3:15)
"For every loan, our Deterministic Reviewer Engine synthesizes all five dimensions into a human-readable narrative. 
It explicitly outlines the top drivers and automatically generates grounded investigation questions for the analyst. And to guarantee zero hallucination, every single number on this screen maps directly to the expandable JSON Evidence Object at the bottom, serialized directly from our Phase 8 pipeline."

### 6. Closing (3:15 - 3:30)
"This is more than a prediction model. It is a fully decoupled intelligence architecture that protects human reviewers from black-box hallucination, separates data failures from credit risk, and provides the exact counterfactual evidence needed to manage a multi-billion-dollar portfolio."
# Evaluator Technical Q&A

**Q: Why LightGBM?**
A: LightGBM natively handles extreme class imbalance (like our 0.04% 12-month default rate) via objective function scaling (`scale_pos_weight`). It also handles categorical features directly without massive one-hot encoding memory explosions, and its raw tree structures integrate seamlessly with `shap.TreeExplainer` for exact marginal contribution calculations.

**Q: Why temporal split?**
A: Random row-wise cross-validation on a longitudinal panel causes massive data leakage because months of the same loan are highly autocorrelated. We enforce a strict chronological split (Train 2018-2021, Valid 2022-2023, Test 2024+) to prove the model can generalize to unseen, future macroeconomic environments.

**Q: Why PR-AUC?**
A: Because the 12-month default target is intensely imbalanced. Traditional ROC-AUC visually inflates performance due to the overwhelming number of True Negatives. PR-AUC focuses strictly on the minority positive class, providing the only true measure of the model's precision and recall at the operational edge.

**Q: How was leakage prevented?**
A: By enforcing the concept of `prediction_month`. All targets are strictly computed looking forward (t+1 to t+12), and all features (Static, Current, Trajectory) are computed using data strictly at or before time `t`.

**Q: Why trajectory features?**
A: A static snapshot of "30 DPD" hides momentum. A loan transitioning from 90 DPD to 30 DPD is curing; a loan moving from Current to 30 DPD is degrading. Adding the 6-month historical trajectory drastically increased PR-AUC from 0.0232 to 0.1579 by capturing this velocity.

**Q: Why reliability is excluded from 12M default?**
A: During Phase 4.1, we proved that Evidence Quality is independent of Credit Risk. Allowing the algorithm to associate missing data with default creates a dangerous feedback loop where bad reporting pipelines trigger false credit alarms.

**Q: Why Aalen-Johansen?**
A: Standard Kaplan-Meier survival curves wildly overestimate default risk because they treat Prepayments as standard right-censoring. Aalen-Johansen explicitly models competing terminal risks, correctly absorbing prepayments as an alternative absorbing state.

**Q: Why competing risks?**
A: In mortgages, if a loan prepays (refinances), it mathematically cannot default in the future. Failing to isolate this competition mathematically corrupts the default incidence curve.

**Q: Why Isolation Forest?**
A: Anomaly detection requires identifying loans that deviate statistically from the portfolio mass without strictly relying on target labels. Isolation Forests efficiently partition the feature space, isolating behavioral deviations regardless of whether the loan ultimately defaulted.

**Q: Why transition surprise?**
A: We convert portfolio-wide empirical Markov transition probabilities into bits of information (`-log2(p)`). This instantly quantifies how "unprecedented" a state change is, mathematically flagging Black Swan jumps (e.g. Current -> Foreclosure in one month).

**Q: Why scenario simulation?**
A: Point-in-time probability is fragile. Scenario simulations apply deterministic counterfactuals (e.g. +1 DPD) to the current feature vector and re-run the margin, calculating the absolute sensitivity delta to expose hidden downside risk.

**Q: Why no fabricated macro scenarios?**
A: Because the official Intain macro_scenarios.csv was not available. Fabricating GDP or unemployment mapping would introduce unscientific causal assumptions into the system. We strictly constrained scenarios to Project-Defined, loan-level feature perturbations.

**Q: Why SHAP?**
A: It provides mathematically exact, additive marginal contributions for every feature for a specific prediction, ensuring the Reviewer Application explains *exactly* what the LightGBM tree executed locally, rather than relying on generalized global feature importance.

**Q: Why LLM?**
A: To synthesize the massively multidimensional Phase 8 Evidence JSON (Risk, Reliability, Anomaly, Trajectory, Scenarios) into a rapid, human-readable narrative, generating highly contextual investigation queries for human analysts.

**Q: How is hallucination controlled?**
A: Via a programmatic Hallucination Guard. The system scans the generated text and asserts that the decimals, anomaly severities, and reliability labels mathematically match the original JSON evidence block. Any deviation triggers an `INVALID` rejection.

**Q: What happens without the LLM?**
A: The pipeline falls back natively to the `DeterministicReviewer` templating engine. This ensures that in isolated, high-security financial environments where live API calls are prohibited, the intelligence dashboard remains 100% operational.

**Q: What are the limitations?**
A: The system lacks external Servicer Notes which limits behavioral context. Also, the 12-month future targets at the very edge of the 2025 panel suffer from administrative right-censoring, which requires dropping those tail-end snapshots.

**Q: What would you build next with real servicer/macro data?**
A: We would integrate the actual macroeconomic indicators as baseline features to shift the Scenario Engine from local counterfactual sensitivity to true causal economic stress testing. We would also embed the textual Servicer Notes into the Anomaly Engine using NLP embeddings.
