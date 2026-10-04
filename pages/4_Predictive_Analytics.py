import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_sensor_data, load_equipment_master, load_failure_events
from utils.analytics import compute_failure_probability, generate_root_cause_summary
from utils.ui import chat_fab

st.header("Predictive Analytics — Die Failure Prediction")

sensor_df = load_sensor_data()
equipment_df = load_equipment_master()
failure_df = load_failure_events()
eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))

# --- Failure Probability per Die ---
st.subheader("Die Failure Risk Overview")
predictions = []
for _, eq in equipment_df.iterrows():
    eq_id = eq["Equipment_ID"]
    eq_sensor = sensor_df[sensor_df["Equipment_ID"] == eq_id].sort_values("Timestamp")
    pred = compute_failure_probability(eq_sensor)
    pred["Equipment_ID"] = eq_id
    pred["Equipment_Name"] = eq["Name"]
    predictions.append(pred)

cols = st.columns(len(predictions))
for col, pred in zip(cols, predictions):
    icon = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(pred["risk_level"], "⚪")
    col.metric(pred["Equipment_Name"], f"{pred['probability']:.0%}", f"{icon} {pred['risk_level']}")

# Risk comparison chart
st.subheader("Failure Probability Comparison")
risk_df = pd.DataFrame([{
    "Die": p["Equipment_Name"], "Probability": p["probability"], "Risk": p["risk_level"],
} for p in predictions])
fig = px.bar(
    risk_df, x="Die", y="Probability", color="Risk",
    color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e67e22", "Critical": "#e74c3c"},
    title="Die Failure Probability",
)
fig.update_layout(height=350, yaxis_tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

# --- Root Cause Investigation ---
st.subheader("Root Cause Investigation")
selected_eq = st.selectbox("Select Die", equipment_df["Equipment_ID"].tolist(), format_func=lambda x: f"{x} — {eq_names[x]}")

eq_pred = next(p for p in predictions if p["Equipment_ID"] == selected_eq)
summary = generate_root_cause_summary(eq_names[selected_eq], eq_pred["top_factors"], failure_df, selected_eq)
st.markdown(summary)

if eq_pred["top_factors"]:
    factor_df = pd.DataFrame(eq_pred["top_factors"], columns=["Factor", "Score"])
    fig = px.bar(factor_df, x="Score", y="Factor", orientation="h", title="Contributing Factors",
                 color="Score", color_continuous_scale="OrRd")
    fig.update_layout(height=250, xaxis_tickformat=".0%", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# --- Remaining Useful Life ---
st.subheader("Estimated Die Remaining Useful Life")
for pred in predictions:
    prob = pred["probability"]
    rul_strokes = int((1 - prob) * 50000)  # ~50k strokes between major services
    rul_hrs = rul_strokes // 10  # ~10 strokes/min
    st.markdown(f"**{pred['Equipment_Name']}**: ~{rul_strokes:,} strokes ({rul_hrs:,} production minutes)")

# --- Failure History ---
st.subheader("Historical Die Failure Patterns")
eq_failures = failure_df[failure_df["Equipment_ID"] == selected_eq]
if eq_failures.empty:
    st.info("No failure history for this die.")
else:
    fig = px.histogram(eq_failures, x="Failure_Mode", color="Failure_Mode", title="Failure Mode Distribution")
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(eq_failures.sort_values("Timestamp", ascending=False), use_container_width=True)

chat_fab()
