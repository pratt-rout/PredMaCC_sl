import streamlit as st
import os

st.set_page_config(page_title="PredMaCC", page_icon=":factory:", layout="wide")

st.title("Predictive Maintenance Command Center")
st.markdown("**Car Door Panel Stamping Press — Die & Tooling Monitoring**")
st.markdown(
    "Converging OT die sensor streams (force, temperature, pressure, strain, vibration, position, proximity) with ERP & maintenance data to predict die failures, automate work orders, and lift OEE."
)
st.info("Use the sidebar to navigate between dashboards.")

_img_path = os.path.join(os.path.dirname(__file__), "PredMACC.png")
try:
    with open(_img_path, "rb") as f:
        st.image(f.read(), use_column_width=True)
except Exception:
    pass
