import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_sensor_data, load_equipment_master
from utils.analytics import SENSOR_COLS, SENSOR_THRESHOLDS
from utils.ui import chat_fab

st.header("Die Sensor Monitoring")

sensor_df = load_sensor_data()
equipment_df = load_equipment_master()
eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))

# Filters
selected_eq = st.selectbox("Select Die", equipment_df["Equipment_ID"].tolist(), format_func=lambda x: f"{x} — {eq_names[x]}")
selected_sensors = st.multiselect("Select Sensors", SENSOR_COLS, default=SENSOR_COLS)

eq_data = sensor_df[sensor_df["Equipment_ID"] == selected_eq].sort_values("Timestamp")

if eq_data.empty:
    st.warning("No sensor data for selected die.")
    st.stop()

# Latest readings
st.subheader("Latest Readings")
cols = st.columns(min(len(selected_sensors), 4))
for i, sensor in enumerate(selected_sensors):
    col = cols[i % len(cols)]
    val = eq_data[sensor].iloc[-1]
    delta = eq_data[sensor].diff().iloc[-1]
    unit = {"Die_Force_kN": "kN", "Die_Temperature_C": "C", "Cushion_Pressure_bar": "bar",
            "Die_Strain_uE": "uE", "Vibration_g": "g", "Ram_Position_mm": "mm", "Proximity_mm": "mm"}.get(sensor, "")
    col.metric(sensor.replace("_", " "), f"{val:.2f} {unit}", f"{delta:+.3f}")

# Time series with thresholds
st.subheader("Sensor Trends")
for sensor in selected_sensors:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq_data["Timestamp"], y=eq_data[sensor], mode="lines", name=sensor))

    anomalies = eq_data[eq_data["Is_Anomaly"] == 1]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["Timestamp"], y=anomalies[sensor],
            mode="markers", name="Anomaly", marker=dict(color="red", size=5),
        ))

    th = SENSOR_THRESHOLDS.get(sensor, {})
    if "warn" in th and "warn_low" not in th:
        fig.add_hline(y=th["warn"], line_dash="dash", line_color="orange", annotation_text="Warning")
        fig.add_hline(y=th["critical"], line_dash="dash", line_color="red", annotation_text="Critical")
    elif "warn_low" in th:
        fig.add_hline(y=th["warn_low"], line_dash="dash", line_color="orange")
        fig.add_hline(y=th["warn_high"], line_dash="dash", line_color="orange")
        fig.add_hline(y=th["critical_low"], line_dash="dash", line_color="red")
        fig.add_hline(y=th["critical_high"], line_dash="dash", line_color="red")

    fig.update_layout(title=sensor.replace("_", " "), height=280, margin=dict(l=40, r=20, t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

# Stroke count trend
st.subheader("Cumulative Stroke Count")
fig = px.line(eq_data, x="Timestamp", y="Stroke_Count", title="Stroke Count Over Time")
fig.update_layout(height=280)
st.plotly_chart(fig, use_container_width=True)

# Correlation heatmap
st.subheader("Die Sensor Correlation")
corr = eq_data[SENSOR_COLS].corr()
fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                title="Sensor Correlation Matrix",
                labels=dict(x="Sensor", y="Sensor"))
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Raw Sensor Data"):
    st.dataframe(eq_data, use_container_width=True)

chat_fab()
