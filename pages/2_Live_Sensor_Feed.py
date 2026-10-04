import time
import streamlit as st
import plotly.graph_objects as go
from utils.data_loader import load_sensor_data, load_equipment_master
from utils.analytics import SENSOR_COLS

st.header("Live Sensor Feed")

sensor_df = load_sensor_data()
equipment_df = load_equipment_master()
eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))

# --- sidebar controls ---
selected_eq = st.sidebar.selectbox(
    "Die",
    equipment_df["Equipment_ID"].tolist(),
    format_func=lambda x: f"{x} — {eq_names[x]}",
)
selected_sensors = st.sidebar.multiselect(
    "Sensors", SENSOR_COLS, default=SENSOR_COLS[:3]
)
window_size = st.sidebar.slider("Window (readings)", 30, 200, 60)
speed = st.sidebar.slider("Speed (ms between ticks)", 100, 2000, 500, step=100)

eq_data = (
    sensor_df[sensor_df["Equipment_ID"] == selected_eq]
    .sort_values("Timestamp")
    .reset_index(drop=True)
)

if eq_data.empty:
    st.warning("No sensor data for selected die.")
    st.stop()

if not selected_sensors:
    st.info("Select at least one sensor from the sidebar.")
    st.stop()

# --- session state for playback position ---
state_key = f"_live_pos_{selected_eq}"
if state_key not in st.session_state:
    st.session_state[state_key] = window_size

col1, col2, col3 = st.sidebar.columns(3)
if col1.button("⏮ Reset"):
    st.session_state[state_key] = window_size
if col2.button("⏸ Pause"):
    st.session_state["_live_running"] = False
if col3.button("▶ Play"):
    st.session_state["_live_running"] = True

running = st.session_state.get("_live_running", True)

# --- metric + chart placeholders ---
metric_area = st.empty()
chart_placeholders = {s: st.empty() for s in selected_sensors}
status_bar = st.empty()

pos = st.session_state[state_key]
total = len(eq_data)

while running and pos < total:
    window = eq_data.iloc[max(0, pos - window_size) : pos]
    latest = window.iloc[-1]
    prev = window.iloc[-2] if len(window) > 1 else latest

    # metrics row
    with metric_area.container():
        ts_label = latest["Timestamp"].strftime("%Y-%m-%d %H:%M")
        st.caption(f"Timestamp: **{ts_label}**  |  Reading {pos}/{total}")
        cols = st.columns(min(len(selected_sensors), 4))
        units = {
            "Die_Force_kN": "kN",
            "Die_Temperature_C": "°C",
            "Cushion_Pressure_bar": "bar",
            "Die_Strain_uE": "µε",
            "Vibration_g": "g",
            "Ram_Position_mm": "mm",
            "Proximity_mm": "mm",
        }
        for i, sensor in enumerate(selected_sensors):
            val = latest[sensor]
            delta = val - prev[sensor]
            cols[i % len(cols)].metric(
                sensor.replace("_", " "),
                f"{val:.2f} {units.get(sensor, '')}",
                f"{delta:+.3f}",
            )

    # charts
    for sensor in selected_sensors:
        x_vals = [t.to_pydatetime() for t in window["Timestamp"]]
        y_vals = [float(v) for v in window[sensor]]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name=sensor,
                line=dict(width=2),
            )
        )
        anomalies = window[window["Is_Anomaly"] == 1]
        if not anomalies.empty:
            fig.add_trace(
                go.Scatter(
                    x=[t.to_pydatetime() for t in anomalies["Timestamp"]],
                    y=[float(v) for v in anomalies[sensor]],
                    mode="markers",
                    name="Anomaly",
                    marker=dict(color="red", size=7, symbol="x"),
                )
            )
        fig.update_layout(
            title=sensor.replace("_", " "),
            height=250,
            margin=dict(l=40, r=20, t=40, b=30),
            xaxis_title="",
            yaxis_title="",
            showlegend=False,
        )
        fig.update_yaxes(autorange=True)
        chart_placeholders[sensor].plotly_chart(fig, use_container_width=True)

    pos += 1
    st.session_state[state_key] = pos
    time.sleep(speed / 1000)

if pos >= total:
    st.session_state[state_key] = window_size
elif not running:
    status_bar.info(f"Paused at reading {pos}/{total}. Press ▶ Play to resume.")
