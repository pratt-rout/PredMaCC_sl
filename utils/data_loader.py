"""Cached data loaders for all PredMaCC datasets."""

import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "dataset"


@st.cache_data
def load_sensor_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sensor_data.csv", parse_dates=["Timestamp"])
    return df


@st.cache_data
def load_equipment_master() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "equipment_master.csv")


@st.cache_data
def load_maintenance_log() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "maintenance_log.csv", parse_dates=["Date"])
    return df


@st.cache_data
def load_work_orders() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "work_orders.csv", parse_dates=["Created", "Due_Date"])
    return df


@st.cache_data
def load_failure_events() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "failure_events.csv", parse_dates=["Timestamp"])
    return df
