import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_work_orders, load_equipment_master, load_sensor_data
from utils.analytics import compute_failure_probability
from utils.ui import chat_fab

st.header("Work Orders — Die Maintenance")

work_orders_df = load_work_orders()
equipment_df = load_equipment_master()
sensor_df = load_sensor_data()
eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))
work_orders_df = work_orders_df.copy()
work_orders_df["Die_Name"] = work_orders_df["Equipment_ID"].map(eq_names)

# Filters
col1, col2, col3 = st.columns(3)
status_filter = col1.multiselect("Status", work_orders_df["Status"].unique().tolist(), default=work_orders_df["Status"].unique().tolist())
priority_filter = col2.multiselect("Priority", work_orders_df["Priority"].unique().tolist(), default=work_orders_df["Priority"].unique().tolist())
eq_filter = col3.multiselect("Die", equipment_df["Equipment_ID"].tolist(), default=equipment_df["Equipment_ID"].tolist(),
                              format_func=lambda x: f"{x} — {eq_names[x]}")

filtered = work_orders_df[
    (work_orders_df["Status"].isin(status_filter)) &
    (work_orders_df["Priority"].isin(priority_filter)) &
    (work_orders_df["Equipment_ID"].isin(eq_filter))
]

# KPIs
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total WOs", len(filtered))
c2.metric("Open", len(filtered[filtered["Status"] == "Open"]))
c3.metric("In Progress", len(filtered[filtered["Status"] == "In Progress"]))
c4.metric("Overdue", len(filtered[filtered["Status"] == "Overdue"]))

# Table
st.subheader("Work Orders")
st.dataframe(
    filtered[["WO_ID", "Die_Name", "Priority", "Status", "Assigned_To", "Description", "Created", "Due_Date"]]
    .sort_values("Created", ascending=False),
    use_container_width=True,
)

# Charts
col_a, col_b = st.columns(2)
with col_a:
    fig = px.histogram(filtered, x="Priority", color="Priority",
                       color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e67e22", "Critical": "#e74c3c"},
                       title="Priority Distribution")
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with col_b:
    fig = px.histogram(filtered, x="Status", color="Status", title="Status Distribution")
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Technician workload
st.subheader("Technician Workload")
tech_load = filtered.groupby("Assigned_To").size().reset_index(name="Count").sort_values("Count", ascending=False)
fig = px.bar(tech_load, x="Assigned_To", y="Count", title="Work Orders per Technician", color="Count", color_continuous_scale="Blues")
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# Auto-suggested WOs from predictions
st.subheader("Suggested Work Orders (from Die Predictions)")
for _, eq in equipment_df.iterrows():
    eq_sensor = sensor_df[sensor_df["Equipment_ID"] == eq["Equipment_ID"]].sort_values("Timestamp")
    pred = compute_failure_probability(eq_sensor)
    if pred["probability"] > 0.3:
        factors_str = ", ".join(f[0] for f in pred["top_factors"])
        st.warning(
            f"**{eq['Name']}** ({eq['Equipment_ID']}) — {pred['probability']:.0%} failure risk. "
            f"Factors: {factors_str}. Consider scheduling die inspection or preventive tryout."
        )

chat_fab()
