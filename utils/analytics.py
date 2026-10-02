"""Analytics helpers for stamping press die monitoring: OEE, anomaly detection, failure prediction."""

import pandas as pd
import numpy as np

SENSOR_COLS = [
    "Die_Force_kN", "Die_Temperature_C", "Cushion_Pressure_bar",
    "Die_Strain_uE", "Vibration_g", "Ram_Position_mm", "Proximity_mm",
]

SENSOR_THRESHOLDS = {
    "Die_Force_kN": {"warn_low": 700, "warn_high": 1000, "critical_low": 650, "critical_high": 1050},
    "Die_Temperature_C": {"warn": 60, "critical": 70},
    "Cushion_Pressure_bar": {"warn_low": 9.5, "warn_high": 15, "critical_low": 8.5, "critical_high": 17},
    "Die_Strain_uE": {"warn": 1500, "critical": 1700},
    "Vibration_g": {"warn": 2.0, "critical": 2.5},
    "Ram_Position_mm": {"warn": 0.8, "critical": 1.0},        # absolute deviation
    "Proximity_mm": {"warn_low": 1.2, "warn_high": 3.8, "critical_low": 1.0, "critical_high": 4.0},
}


def detect_anomalies(df: pd.DataFrame, window: int = 24, z_thresh: float = 2.5) -> pd.DataFrame:
    results = []
    for eq_id, grp in df.groupby("Equipment_ID"):
        grp = grp.sort_values("Timestamp").copy()
        for col in SENSOR_COLS:
            roll_mean = grp[col].rolling(window, min_periods=1).mean()
            roll_std = grp[col].rolling(window, min_periods=1).std().fillna(1)
            grp[f"{col}_zscore"] = ((grp[col] - roll_mean) / roll_std).abs()
        grp["Anomaly_Score"] = grp[[f"{c}_zscore" for c in SENSOR_COLS]].max(axis=1)
        grp["Is_Anomaly_Calc"] = (grp["Anomaly_Score"] > z_thresh).astype(int)
        results.append(grp)
    return pd.concat(results, ignore_index=True)


def compute_health_score(df_eq: pd.DataFrame) -> float:
    if df_eq.empty:
        return 100.0
    latest = df_eq.tail(24)
    penalties = 0
    for col, thresh in SENSOR_THRESHOLDS.items():
        vals = latest[col] if col != "Ram_Position_mm" else latest[col].abs()
        if "warn" in thresh and "warn_low" not in thresh:
            penalties += (vals > thresh["warn"]).sum() * 2
            penalties += (vals > thresh["critical"]).sum() * 5
        elif "warn_low" in thresh:
            penalties += ((vals < thresh["warn_low"]) | (vals > thresh["warn_high"])).sum() * 2
            penalties += ((vals < thresh["critical_low"]) | (vals > thresh["critical_high"])).sum() * 5
    return max(0, 100 - penalties)


def compute_failure_probability(df_eq: pd.DataFrame) -> dict:
    if len(df_eq) < 48:
        return {"probability": 0.0, "risk_level": "Low", "top_factors": []}

    recent = df_eq.tail(48)
    factors = []

    # Force drift
    force_trend = recent["Die_Force_kN"].diff().mean()
    if abs(force_trend) > 1.0:
        factors.append(("Die Force Drift", min(abs(force_trend) / 5, 1.0)))

    # Temperature rise
    temp_mean = recent["Die_Temperature_C"].mean()
    if temp_mean > 55:
        factors.append(("Elevated Die Temperature", min((temp_mean - 45) / 30, 1.0)))

    # Vibration
    vib_mean = recent["Vibration_g"].mean()
    if vib_mean > 1.5:
        factors.append(("High Vibration", min((vib_mean - 1.0) / 2.0, 1.0)))

    # Strain
    strain_mean = recent["Die_Strain_uE"].mean()
    if strain_mean > 1400:
        factors.append(("Excessive Die Strain", min((strain_mean - 1200) / 600, 1.0)))

    # Position deviation
    pos_std = recent["Ram_Position_mm"].std()
    if pos_std > 0.3:
        factors.append(("Ram Position Instability", min(pos_std / 1.0, 1.0)))

    # Proximity drift (die clearance)
    prox_std = recent["Proximity_mm"].std()
    if prox_std > 0.2:
        factors.append(("Die Clearance Variation", min(prox_std / 0.5, 1.0)))

    # Pressure fluctuation
    pres_std = recent["Cushion_Pressure_bar"].std()
    if pres_std > 0.5:
        factors.append(("Cushion Pressure Fluctuation", min(pres_std / 2.0, 1.0)))

    # Anomaly rate
    anomaly_rate = recent["Is_Anomaly"].mean()
    if anomaly_rate > 0.1:
        factors.append(("Anomaly Rate", min(anomaly_rate * 2, 1.0)))

    if not factors:
        return {"probability": 0.05, "risk_level": "Low", "top_factors": []}

    prob = min(sum(f[1] for f in factors) / len(factors), 0.95)
    risk = "Low" if prob < 0.3 else "Medium" if prob < 0.6 else "High" if prob < 0.8 else "Critical"
    factors.sort(key=lambda x: x[1], reverse=True)

    return {
        "probability": round(prob, 3),
        "risk_level": risk,
        "top_factors": factors[:4],
    }


def compute_oee(sensor_df, maintenance_df, failure_df, equipment_id) -> dict:
    eq_sensor = sensor_df[sensor_df["Equipment_ID"] == equipment_id]
    eq_failures = failure_df[failure_df["Equipment_ID"] == equipment_id]
    eq_maint = maintenance_df[maintenance_df["Equipment_ID"] == equipment_id]

    total_hours = len(eq_sensor)
    if total_hours == 0:
        return {"availability": 0, "performance": 0, "quality": 0, "oee": 0}

    downtime_hrs = eq_failures["Downtime_hrs"].sum() + eq_maint["Duration_hrs"].sum() * 0.3
    availability = max(0, (total_hours - downtime_hrs) / total_hours)

    # Performance: actual stroke rate vs ideal
    if "Stroke_Count" in eq_sensor.columns:
        total_strokes = eq_sensor["Stroke_Count"].iloc[-1]
        ideal_strokes = total_hours * 10  # 10 strokes/min ideal
        performance = min(total_strokes / ideal_strokes, 1.0) if ideal_strokes > 0 else 1.0
    else:
        performance = 0.92

    quality = 1 - eq_sensor["Is_Anomaly"].mean()

    oee = availability * performance * quality
    return {
        "availability": round(availability * 100, 1),
        "performance": round(performance * 100, 1),
        "quality": round(quality * 100, 1),
        "oee": round(oee * 100, 1),
    }


def generate_root_cause_summary(eq_name, factors, failure_df, eq_id) -> str:
    eq_failures = failure_df[failure_df["Equipment_ID"] == eq_id]
    recent_modes = eq_failures.tail(3)["Failure_Mode"].tolist() if not eq_failures.empty else []

    lines = [f"**{eq_name}** — Die Health Risk Assessment:"]
    if factors:
        lines.append("Contributing factors (ranked by severity):")
        for name, score in factors:
            bar = "\u2588" * int(score * 10) + "\u2591" * (10 - int(score * 10))
            lines.append(f"  - {name}: {bar} ({score:.0%})")
    if recent_modes:
        lines.append(f"Historical failure patterns: {', '.join(recent_modes)}")
        lines.append("Recommend die inspection focusing on wear surfaces, guide clearances, and thermal management.")
    else:
        lines.append("No recent failure history. Continue monitoring sensor trends and scheduled tryouts.")
    return "\n".join(lines)
