"""Alert generation from die sensor thresholds."""

import pandas as pd
from utils.analytics import SENSOR_THRESHOLDS


def generate_alerts(sensor_df: pd.DataFrame, equipment_df: pd.DataFrame) -> pd.DataFrame:
    alerts = []
    eq_names = dict(zip(equipment_df["Equipment_ID"], equipment_df["Name"]))

    for eq_id, grp in sensor_df.groupby("Equipment_ID"):
        latest = grp.sort_values("Timestamp").iloc[-1]
        name = eq_names.get(eq_id, eq_id)

        # Die Force
        v = latest["Die_Force_kN"]
        th = SENSOR_THRESHOLDS["Die_Force_kN"]
        if v < th["critical_low"] or v > th["critical_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Die Force", f"{v:.0f} kN outside critical range ({th['critical_low']}-{th['critical_high']})"))
        elif v < th["warn_low"] or v > th["warn_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Die Force", f"{v:.0f} kN outside normal range ({th['warn_low']}-{th['warn_high']})"))

        # Die Temperature
        v = latest["Die_Temperature_C"]
        th = SENSOR_THRESHOLDS["Die_Temperature_C"]
        if v > th["critical"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Die Temperature", f"{v:.1f} C exceeds critical ({th['critical']} C)"))
        elif v > th["warn"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Die Temperature", f"{v:.1f} C exceeds warning ({th['warn']} C)"))

        # Cushion Pressure
        v = latest["Cushion_Pressure_bar"]
        th = SENSOR_THRESHOLDS["Cushion_Pressure_bar"]
        if v < th["critical_low"] or v > th["critical_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Cushion Pressure", f"{v:.1f} bar outside critical range"))
        elif v < th["warn_low"] or v > th["warn_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Cushion Pressure", f"{v:.1f} bar outside normal range"))

        # Die Strain
        v = latest["Die_Strain_uE"]
        th = SENSOR_THRESHOLDS["Die_Strain_uE"]
        if v > th["critical"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Die Strain", f"{v:.0f} uE exceeds critical ({th['critical']})"))
        elif v > th["warn"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Die Strain", f"{v:.0f} uE exceeds warning ({th['warn']})"))

        # Vibration
        v = latest["Vibration_g"]
        th = SENSOR_THRESHOLDS["Vibration_g"]
        if v > th["critical"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Vibration", f"{v:.2f} g exceeds critical ({th['critical']})"))
        elif v > th["warn"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Vibration", f"{v:.2f} g exceeds warning ({th['warn']})"))

        # Ram Position (absolute deviation)
        v = abs(latest["Ram_Position_mm"])
        th = SENSOR_THRESHOLDS["Ram_Position_mm"]
        if v > th["critical"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Ram Position", f"{v:.3f} mm deviation exceeds critical ({th['critical']})"))
        elif v > th["warn"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Ram Position", f"{v:.3f} mm deviation exceeds warning ({th['warn']})"))

        # Proximity (die clearance)
        v = latest["Proximity_mm"]
        th = SENSOR_THRESHOLDS["Proximity_mm"]
        if v < th["critical_low"] or v > th["critical_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Critical", "Die Clearance", f"{v:.2f} mm outside critical range ({th['critical_low']}-{th['critical_high']})"))
        elif v < th["warn_low"] or v > th["warn_high"]:
            alerts.append(_alert(latest["Timestamp"], eq_id, name, "Warning", "Die Clearance", f"{v:.2f} mm outside normal range ({th['warn_low']}-{th['warn_high']})"))

    if not alerts:
        return pd.DataFrame(columns=["Timestamp", "Equipment_ID", "Equipment_Name", "Severity", "Sensor", "Message"])
    return pd.DataFrame(alerts).sort_values("Severity", ascending=True)


def _alert(ts, eq_id, name, severity, sensor, msg):
    return {
        "Timestamp": ts,
        "Equipment_ID": eq_id,
        "Equipment_Name": name,
        "Severity": severity,
        "Sensor": sensor,
        "Message": msg,
    }
