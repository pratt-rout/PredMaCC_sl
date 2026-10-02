import streamlit as st
from utils.data_loader import load_equipment_master, load_sensor_data

st.set_page_config(page_title="PredMaCC", page_icon=":factory:", layout="wide")

st.sidebar.title("PredMaCC")
st.sidebar.caption("Predictive Maintenance Command Center — Car Door Panel Stamping Press")

equipment_df = load_equipment_master()
sensor_df = load_sensor_data()

st.sidebar.header("Global Filters")
eq_options = ["All"] + equipment_df["Equipment_ID"].tolist()
selected_eq = st.sidebar.selectbox("Equipment", eq_options)
if selected_eq != "All":
    st.session_state["selected_equipment"] = selected_eq
else:
    st.session_state["selected_equipment"] = None

date_min = sensor_df["Timestamp"].min().date()
date_max = sensor_df["Timestamp"].max().date()
date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
if len(date_range) == 2:
    st.session_state["date_range"] = date_range
else:
    st.session_state["date_range"] = (date_min, date_max)

st.title("Predictive Maintenance Command Center")
st.markdown("**Car Door Panel Stamping Press — Die & Tooling Monitoring**")
st.markdown("Converging OT die sensor streams (force, temperature, pressure, strain, vibration, position, proximity) with ERP & maintenance data to predict die failures, automate work orders, and lift OEE.")
st.info("Use the sidebar to navigate between dashboards. Select a specific die or date range to filter across all pages.")
