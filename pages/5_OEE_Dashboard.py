import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_sensor_data, load_equipment_master, load_maintenance_log, load_failure_events
from utils.analytics import compute_oee

st.header("OEE Dashboard — Stamping Press Dies")

sensor_df = load_sensor_data()
equipment_df = load_equipment_master()
maintenance_df = load_maintenance_log()
failure_df = load_failure_events()

# Compute OEE for all dies
oee_results = []
for _, eq in equipment_df.iterrows():
    oee = compute_oee(sensor_df, maintenance_df, failure_df, eq["Equipment_ID"])
    oee["Equipment_ID"] = eq["Equipment_ID"]
    oee["Die_Name"] = eq["Name"]
    oee_results.append(oee)

oee_df = pd.DataFrame(oee_results)

# Plant-level OEE
avg_oee = oee_df["oee"].mean()
avg_avail = oee_df["availability"].mean()
avg_perf = oee_df["performance"].mean()
avg_qual = oee_df["quality"].mean()

st.subheader("Press Line OEE")
c1, c2, c3, c4 = st.columns(4)
c1.metric("OEE", f"{avg_oee:.1f}%")
c2.metric("Availability", f"{avg_avail:.1f}%")
c3.metric("Performance", f"{avg_perf:.1f}%")
c4.metric("Quality", f"{avg_qual:.1f}%")

def make_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, 60], "color": "#fee"}, {"range": [60, 85], "color": "#ffd"}, {"range": [85, 100], "color": "#dfd"}]},
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

g1, g2, g3, g4 = st.columns(4)
g1.plotly_chart(make_gauge(avg_oee, "OEE", "#3498db"), use_container_width=True)
g2.plotly_chart(make_gauge(avg_avail, "Availability", "#2ecc71"), use_container_width=True)
g3.plotly_chart(make_gauge(avg_perf, "Performance", "#f39c12"), use_container_width=True)
g4.plotly_chart(make_gauge(avg_qual, "Quality", "#9b59b6"), use_container_width=True)

# Die-level OEE breakdown
st.subheader("Die-Level OEE Breakdown")
fig = px.bar(
    oee_df, x="Die_Name", y=["availability", "performance", "quality"],
    barmode="group", title="OEE Components by Die",
    labels={"value": "%", "Die_Name": "Die", "variable": "Component"},
    color_discrete_map={"availability": "#2ecc71", "performance": "#f39c12", "quality": "#9b59b6"},
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

fig2 = px.bar(oee_df, x="Die_Name", y="oee", color="oee",
              color_continuous_scale="RdYlGn", range_color=[0, 100],
              title="Overall OEE by Die")
fig2.update_layout(height=350)
st.plotly_chart(fig2, use_container_width=True)

# Downtime Pareto
st.subheader("Die Failure Downtime Pareto")
failure_agg = failure_df.groupby("Failure_Mode")["Downtime_hrs"].sum().sort_values(ascending=False).reset_index()
failure_agg["Cumulative_%"] = (failure_agg["Downtime_hrs"].cumsum() / failure_agg["Downtime_hrs"].sum() * 100)

fig3 = go.Figure()
fig3.add_trace(go.Bar(x=failure_agg["Failure_Mode"], y=failure_agg["Downtime_hrs"], name="Downtime (hrs)", marker_color="#e74c3c"))
fig3.add_trace(go.Scatter(x=failure_agg["Failure_Mode"], y=failure_agg["Cumulative_%"], name="Cumulative %", yaxis="y2", line=dict(color="#3498db", width=2)))
fig3.update_layout(
    title="Downtime Pareto — Die Failure Modes", height=400,
    yaxis=dict(title="Downtime (hours)"),
    yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
)
st.plotly_chart(fig3, use_container_width=True)

# Maintenance cost
st.subheader("Die Maintenance Cost by Type")
cost_by_type = maintenance_df.groupby("Type")["Cost_INR"].sum().reset_index()
fig4 = px.pie(cost_by_type, values="Cost_INR", names="Type", title="Maintenance Cost Distribution (INR)",
              color_discrete_sequence=px.colors.qualitative.Set2)
fig4.update_layout(height=350)
st.plotly_chart(fig4, use_container_width=True)
