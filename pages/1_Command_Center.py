import streamlit as st
import plotly.express as px
from utils.data_loader import (
    load_sensor_data, load_equipment_master, load_failure_events, load_work_orders,
)
from utils.alerts import generate_alerts
from utils.analytics import compute_health_score
from utils.ui import chat_fab

st.header("Command Center — Die Alert Triage")

sensor_df = load_sensor_data()
equipment_df = load_equipment_master()
failure_df = load_failure_events()
work_orders_df = load_work_orders()

# --- Active Alerts ---
st.subheader("Active Die Alerts")
alerts_df = generate_alerts(sensor_df, equipment_df)
if alerts_df.empty:
    st.success("All die sensors within normal range — no active alerts.")
else:
    crit = len(alerts_df[alerts_df["Severity"] == "Critical"])
    warn = len(alerts_df[alerts_df["Severity"] == "Warning"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Critical", crit)
    c2.metric("Warning", warn)
    c3.metric("Total Alerts", len(alerts_df))

    for _, row in alerts_df.iterrows():
        icon = "🔴" if row["Severity"] == "Critical" else "🟡"
        st.markdown(f"{icon} **{row['Equipment_Name']}** ({row['Equipment_ID']}) — {row['Sensor']}: {row['Message']}")

# --- Die Health Summary ---
st.subheader("Die Health Overview")
cols = st.columns(len(equipment_df))
for col, (_, eq) in zip(cols, equipment_df.iterrows()):
    eq_sensor = sensor_df[sensor_df["Equipment_ID"] == eq["Equipment_ID"]]
    score = compute_health_score(eq_sensor)
    color = "normal" if score >= 70 else ("off" if score >= 40 else "inverse")
    col.metric(eq["Name"], f"{score:.0f}/100", delta_color=color)

# --- Failure Timeline ---
st.subheader("Die Failure Timeline")
if failure_df.empty:
    st.info("No failure events recorded.")
else:
    recent = failure_df.sort_values("Timestamp", ascending=False).head(15)
    eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))
    recent = recent.copy()
    recent["Die_Name"] = recent["Equipment_ID"].map(eq_names)

    fig = px.scatter(
        recent, x="Timestamp", y="Die_Name", color="Failure_Mode",
        size="Downtime_hrs", hover_data=["Root_Cause", "Downtime_hrs"],
        title="Recent Die Failure Events",
    )
    fig.update_layout(height=350, yaxis_title="", xaxis_title="Time")
    st.plotly_chart(fig, use_container_width=True)

# --- Work Order Summary ---
st.subheader("Work Order Status")
wo_counts = work_orders_df["Status"].value_counts().reset_index()
wo_counts.columns = ["Status", "Count"]
fig = px.pie(wo_counts, values="Count", names="Status", title="Work Orders by Status",
             color_discrete_sequence=px.colors.qualitative.Set2)
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

chat_fab()
