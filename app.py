import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="LoanPulse | Reviewer Intelligence", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    ev = pd.read_parquet('data/processed/explanation_evidence.parquet')
    ro = pd.read_parquet('data/processed/reviewer_outputs.parquet')
    df = ev.merge(ro[['loan_id', 'prediction_month', 'reviewer_note']], on=['loan_id', 'prediction_month'], how='left')
    return df

st.title("Loan Performance Intelligence Workspace")

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load artifacts: {e}")
    st.stop()

# 1. Portfolio Intelligence (Sidebar)
st.sidebar.header("Portfolio Intelligence")
total_loans = len(df)
st.sidebar.metric("Total Active Evaluated Loans", f"{total_loans:,}")

# We need to parse priority out of the note or determine it again
def extract_priority(note):
    if not isinstance(note, str): return "ROUTINE"
    if "MUST_REVIEW" in note: return "MUST_REVIEW"
    if "WATCH" in note: return "WATCH"
    return "ROUTINE"

df['priority'] = df['reviewer_note'].apply(extract_priority)
must_review_count = len(df[df['priority'] == 'MUST_REVIEW'])
st.sidebar.metric("MUST_REVIEW Cases", f"{must_review_count:,}")

# 2. Reviewer Queue
st.header("Reviewer Queue")
col1, col2, col3 = st.columns(3)
search_id = col1.text_input("Search Loan ID", "")
filter_priority = col2.selectbox("Filter by Priority", ["ALL", "MUST_REVIEW", "WATCH", "ROUTINE"])

# Filter logic
filtered = df.copy()
if search_id:
    filtered = filtered[filtered['loan_id'].str.contains(search_id, case=False)]
if filter_priority != "ALL":
    filtered = filtered[filtered['priority'] == filter_priority]

# Sort so MUST_REVIEW is on top
priority_map = {'MUST_REVIEW': 0, 'WATCH': 1, 'ROUTINE': 2}
filtered['p_sort'] = filtered['priority'].map(priority_map)
filtered = filtered.sort_values('p_sort').drop('p_sort', axis=1)

# Display Queue
st.dataframe(filtered[['loan_id', 'prediction_month', 'priority', 'must_review_flag']].head(50), use_container_width=True)

if len(filtered) > 0:
    st.markdown("---")
    # Select Loan
    selected_loan = st.selectbox("Select Loan to Investigate", filtered['loan_id'].tolist())
    
    if selected_loan:
        row = filtered[filtered['loan_id'] == selected_loan].iloc[0]
        
        # Parse JSON Evidence
        risk = json.loads(row['risk'])
        rel = json.loads(row['reliability'])
        anom = json.loads(row['anomaly'])
        scen = json.loads(row['scenario'])
        traj = json.loads(row['trajectory'])
        trans = json.loads(row['transition'])
        explanation = json.loads(row['explanation'])
        
        st.header(f"Loan Intelligence View: {selected_loan}")
        
        # 10. Reviewer Note
        st.subheader("🤖 Reviewer Note (Deterministic Fallback) [Live LLM API: AVAILABLE / NOT VERIFIED]")
        st.info(row['reviewer_note'])
        
        # 3. Orthogonal Dimensions
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Risk ({risk['target']})", f"{risk['probability']*100:.2f}%", risk['risk_band'], delta_color="inverse")
        c2.metric("Reliability Score", f"{rel['score']:.1f}", rel['band'], delta_color="normal")
        c3.metric("Anomaly Severity", anom['severity'], delta_color="off")
        c4.metric("Scenario Sensitivity", f"{scen['max_delta_12m_default']*100:+.2f} pts", "Max Delta", delta_color="inverse")
        
        st.markdown("---")
        
        row1_col1, row1_col2 = st.columns(2)
        
        # 4. Risk Explanation
        with row1_col1:
            st.subheader("Risk Explanation")
            st.write(f"**Target Model:** {risk['target']}")
            st.write(f"**Prediction Probability:** {risk['probability']*100:.2f}% ({risk['risk_band']} Band)")
            st.write("**Top Positive Drivers (Pushing Risk Up):**")
            for f in explanation['top_positive_factors']:
                st.write(f"- {f}")
            st.write("**Top Negative Drivers (Pushing Risk Down):**")
            for f in explanation['top_negative_factors']:
                st.write(f"- {f}")
                
        # 5. Trajectory Visualization
        with row1_col2:
            st.subheader("Trajectory Visualization")
            st.write(f"**Recent 6-Month State History:**")
            st.code(traj['recent_states'])
            st.write(f"- Maximum DPD (6M): {traj.get('max_6m_dpd', 'N/A')}")
            st.write(f"- Consecutive Delinquency Months: {traj.get('consecutive_delinq', 'N/A')}")
            st.write(f"- Observed Transitions (6M): {traj.get('observed_transitions_6m', 'N/A')}")
            st.write(f"- Balance Reduction (6M): {traj.get('balance_reduction_6m', 'N/A')}")
            
        st.markdown("---")
        row2_col1, row2_col2 = st.columns(2)
        
        # 7. Reliability Panel
        with row2_col1:
            st.subheader("Reliability Intelligence")
            st.warning("*Reliability measures evidence quality, not credit risk.*")
            st.write(f"**Score:** {rel['score']} ({rel['band']})")
            if len(rel.get('validation_warnings', [])) > 0:
                st.write("**Validation Warnings:**")
                for w in rel.get('validation_warnings', []):
                    st.write(f"- {w}")
            else:
                st.write("No severe deterministic validation warnings.")
                
        # 8. Anomaly Panel
        with row2_col2:
            st.subheader("Anomaly Intelligence")
            st.info("*Anomaly detects rare multidimensional data behaviors, independently of credit risk.*")
            st.write(f"**Severity:** {anom.get('severity', 'N/A')}")
            st.write(f"**Statistical Isolation Score (Behavioral):** {anom.get('isolation_score', 0.0):.3f}")
            
            if len(anom.get('top_anomalous_features', [])) > 0:
                st.write("**Top Anomalous Dimensions:**")
                for f in anom.get('top_anomalous_features', []):
                    st.write(f"- {f}")
            
        # 6. Transition Intelligence
        st.subheader("Transition Intelligence")
        st.write(f"**Observed Transition:** `{trans.get('previous_state', 'N/A')}` → `{trans.get('current_state', 'N/A')}`")
        
        prob = trans.get('probability')
        surp = trans.get('surprise')
        if prob is None or pd.isna(prob):
            st.write("**Expected Probability (Portfolio-Wide):** N/A (New Origination / No History)")
            st.write("**Transition Surprise (bits):** N/A")
        else:
            st.write(f"**Expected Probability (Portfolio-Wide):** {prob*100:.2f}%")
            st.write(f"**Transition Surprise (bits):** {surp:.2f}")
        
        # 9. Scenario Explorer
        st.markdown("---")
        st.subheader("Scenario Explorer")
        st.caption("Model-sensitivity counterfactual — not a causal forecast.")
        
        base_risk = scen.get('baseline_12m_default_risk')
        scen_risk = scen.get('scenario_12m_default_risk')
        delta_risk = scen.get('max_delta_12m_default')
        
        if base_risk is None or pd.isna(base_risk):
            st.write("**Baseline 12m Default Risk:** N/A")
            st.write("**Scenario (Delinquency Shock) Risk:** N/A")
            st.write("**Absolute Delta:** N/A")
        else:
            st.write(f"**Baseline 12m Default Risk:** {base_risk*100:.2f}%")
            st.write(f"**Scenario (Delinquency Shock) Risk:** {scen_risk*100:.2f}%")
            st.write(f"**Absolute Delta:** {delta_risk*100:+.2f} percentage points")
        
        # 11. Evidence Transparency
        with st.expander("View Raw JSON Evidence Object"):
            st.json({
                'risk': risk,
                'reliability': rel,
                'anomaly': anom,
                'scenario': scen,
                'trajectory': traj,
                'transition': trans,
                'explanation': explanation
            })
