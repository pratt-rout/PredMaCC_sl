"""Generate PredMaCC datasets for car door panel stamping press dies."""

import csv
import math
import random
import datetime
import os

random.seed(42)

BASE = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

# --- Die / Tooling Master ---
EQUIPMENT = [
    ("DIE-001", "Front-Left Door Panel Die", "Progressive Die", "Press Line 1 - Station A", "2020-06-10", "Critical"),
    ("DIE-002", "Front-Right Door Panel Die", "Progressive Die", "Press Line 1 - Station B", "2020-06-10", "Critical"),
    ("DIE-003", "Rear-Left Door Panel Die", "Transfer Die", "Press Line 2 - Station A", "2019-11-20", "High"),
    ("DIE-004", "Rear-Right Door Panel Die", "Transfer Die", "Press Line 2 - Station B", "2019-11-20", "High"),
    ("DIE-005", "Tailgate Inner Panel Die", "Tandem Die", "Press Line 3 - Station A", "2021-03-15", "Critical"),
]

TECHNICIANS = ["Rajesh Kumar", "Amit Sharma", "Priya Patel", "Suresh Nair", "Deepak Joshi"]

FAILURE_MODES = [
    ("Die Crack", "Fatigue crack propagation in die insert due to cyclic stamping load"),
    ("Surface Galling", "Adhesive wear on die face from sheet metal sliding under high pressure"),
    ("Misalignment", "Punch-die clearance deviation caused by guide pin wear"),
    ("Thermal Distortion", "Uneven die temperature causing dimensional drift in stamped panel"),
    ("Spring-back Defect", "Excessive elastic recovery in stamped part due to worn die profile"),
    ("Slug Retention", "Slug not ejecting from die cavity - proximity sensor triggered"),
    ("Cushion Pressure Loss", "Hydraulic cushion seal degradation causing uneven blank hold-down"),
]


def write_equipment_master():
    path = os.path.join(DATASET_DIR, "equipment_master.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Equipment_ID", "Name", "Type", "Location", "Install_Date", "Criticality"])
        for eq in EQUIPMENT:
            w.writerow(eq)
    print(f"  equipment_master.csv ({len(EQUIPMENT)} rows)")


def generate_failure_events():
    events = []
    eid = 1
    start = datetime.datetime(2024, 1, 1)
    for eq_id, *_ in EQUIPMENT:
        n_failures = random.randint(3, 8)
        for _ in range(n_failures):
            offset_hrs = random.randint(100, 4900)
            ts = start + datetime.timedelta(hours=offset_hrs)
            mode, cause = random.choice(FAILURE_MODES)
            downtime = round(random.uniform(2, 36), 1)
            events.append((f"FE-{eid:04d}", eq_id, ts, mode, cause, downtime))
            eid += 1
    events.sort(key=lambda x: x[2])
    return events


def write_failure_events(events):
    path = os.path.join(DATASET_DIR, "failure_events.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Event_ID", "Equipment_ID", "Timestamp", "Failure_Mode", "Root_Cause", "Downtime_hrs"])
        for ev in events:
            w.writerow([ev[0], ev[1], ev[2].strftime("%Y-%m-%d %H:%M:%S"), ev[3], ev[4], ev[5]])
    print(f"  failure_events.csv ({len(events)} rows)")


def write_sensor_data(failure_events):
    """5000 rows of per-stroke sensor data (one row per press stroke) with 7 die sensors."""
    failure_map = {}
    for _, eq_id, ts, *_ in failure_events:
        failure_map.setdefault(eq_id, []).append(ts)

    path = os.path.join(DATASET_DIR, "sensor_data.csv")
    start = datetime.datetime(2024, 1, 1, 6, 0, 0)  # shift start 6 AM
    rows = 0

    # Stroke interval ~6 seconds = 10 strokes/min, but we sample every 10th stroke (~1 min)
    stroke_interval = datetime.timedelta(seconds=60)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Timestamp", "Equipment_ID", "Stroke_Count",
            "Die_Force_kN", "Die_Temperature_C", "Cushion_Pressure_bar",
            "Die_Strain_uE", "Vibration_g", "Ram_Position_mm", "Proximity_mm",
            "Is_Anomaly",
        ])

        for eq_id, *_ in EQUIPMENT:
            # Nominal values for a 1000-ton stamping press die
            force = 850.0       # kN — die closing force
            temp = 45.0         # C — die surface temperature
            pressure = 12.0     # bar — cushion / blank-holder pressure
            strain = 1200.0     # micro-strain on die insert
            vib = 0.8           # g RMS
            position = 0.0      # mm — ram bottom-dead-center deviation
            proximity = 2.5     # mm — punch-to-die clearance

            eq_failures = failure_map.get(eq_id, [])
            stroke = 0

            for i in range(1000):
                ts = start + stroke_interval * i
                stroke += random.randint(8, 12)  # strokes since last sample
                hour = ts.hour

                # Thermal drift during shift (dies heat up)
                shift_thermal = 8.0 * math.sin(math.pi * (hour - 6) / 16) if 6 <= hour <= 22 else 0

                # Check proximity to failure
                near_failure = any(
                    0 <= (ft - ts).total_seconds() / 3600 <= 48 for ft in eq_failures
                )
                boost = 1.0
                if near_failure:
                    hrs = min(
                        abs((ft - ts).total_seconds() / 3600)
                        for ft in eq_failures
                        if 0 <= (ft - ts).total_seconds() / 3600 <= 48
                    )
                    boost = 1.0 + (48 - hrs) / 12  # stronger degradation curve

                force = max(600, min(1200, force + random.gauss(0, 5) * boost + (boost - 1) * 15))
                temp = max(30, min(85, temp + shift_thermal * 0.05 + random.gauss(0, 0.4) * boost))
                pressure = max(8, min(18, pressure + random.gauss(0, 0.08) * boost))
                strain = max(800, min(2000, strain + random.gauss(0, 15) * boost + (boost - 1) * 30))
                vib = max(0.2, min(5.0, vib + random.gauss(0, 0.04) * boost + (boost - 1) * 0.08))
                position = max(-2.0, min(2.0, position + random.gauss(0, 0.02) * boost))
                proximity = max(0.5, min(5.0, proximity + random.gauss(0, 0.03) * boost))

                is_anomaly = 1 if (
                    boost > 1.5
                    or force > 1050 or force < 650
                    or temp > 70
                    or vib > 2.5
                    or abs(position) > 1.0
                    or proximity < 1.0 or proximity > 4.0
                    or strain > 1700
                ) else 0

                w.writerow([
                    ts.strftime("%Y-%m-%d %H:%M:%S"), eq_id, stroke,
                    round(force, 1), round(temp, 2), round(pressure, 2),
                    round(strain, 1), round(vib, 3), round(position, 3), round(proximity, 3),
                    is_anomaly,
                ])
                rows += 1

    print(f"  sensor_data.csv ({rows} rows)")


def write_maintenance_log(failure_events):
    path = os.path.join(DATASET_DIR, "maintenance_log.csv")
    records = []
    mid = 1

    start = datetime.datetime(2024, 1, 1)
    for eq_id, name, *_ in EQUIPMENT:
        # Die maintenance intervals: sharpening, polishing, inspection
        interval_days = random.randint(7, 21)
        d = start
        tasks = [
            "Die surface polishing and inspection",
            "Guide pin and bushing clearance check",
            "Hydraulic cushion pressure calibration",
            "Die alignment and shim adjustment",
            "Proximity sensor calibration",
            "Strain gauge zero-drift recalibration",
        ]
        while d < start + datetime.timedelta(days=210):
            records.append((
                f"MNT-{mid:04d}", eq_id, d.strftime("%Y-%m-%d"),
                "Preventive", random.choice(tasks),
                round(random.uniform(2, 8), 1), round(random.uniform(5000, 25000), 2),
            ))
            mid += 1
            d += datetime.timedelta(days=interval_days)

    for _, eq_id, ts, mode, cause, downtime in failure_events:
        mtype = random.choice(["Corrective", "Breakdown"])
        records.append((
            f"MNT-{mid:04d}", eq_id, ts.strftime("%Y-%m-%d"),
            mtype, f"{mtype} repair: {mode} - {cause}",
            round(downtime + random.uniform(1, 8), 1),
            round(random.uniform(15000, 120000), 2),
        ))
        mid += 1

    records.sort(key=lambda x: x[2])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Maintenance_ID", "Equipment_ID", "Date", "Type", "Description", "Duration_hrs", "Cost_INR"])
        for r in records:
            w.writerow(r)
    print(f"  maintenance_log.csv ({len(records)} rows)")


def write_work_orders(failure_events):
    path = os.path.join(DATASET_DIR, "work_orders.csv")
    orders = []
    wid = 1
    statuses = ["Open", "In Progress", "Completed", "Overdue"]
    priorities = ["Low", "Medium", "High", "Critical"]

    for _, eq_id, ts, mode, cause, _ in failure_events:
        created = ts - datetime.timedelta(hours=random.randint(1, 12))
        due = created + datetime.timedelta(days=random.randint(1, 5))
        status = random.choice(statuses)
        priority = random.choices(priorities, weights=[1, 2, 4, 3])[0]
        orders.append((
            f"WO-{wid:04d}", eq_id, created.strftime("%Y-%m-%d %H:%M:%S"),
            priority, status, random.choice(TECHNICIANS),
            f"Investigate {mode}: {cause}", due.strftime("%Y-%m-%d"),
        ))
        wid += 1

    start = datetime.datetime(2024, 1, 1)
    die_checks = [
        "Scheduled die tryout and panel quality audit",
        "Die clearance measurement and adjustment",
        "Blank-holder pressure rebalancing",
        "Proximity sensor functional test",
        "Die temperature sensor validation",
    ]
    for eq_id, name, *_ in EQUIPMENT:
        for _ in range(random.randint(5, 10)):
            created = start + datetime.timedelta(hours=random.randint(0, 4900))
            due = created + datetime.timedelta(days=random.randint(3, 14))
            orders.append((
                f"WO-{wid:04d}", eq_id, created.strftime("%Y-%m-%d %H:%M:%S"),
                random.choice(["Low", "Medium"]),
                random.choice(statuses),
                random.choice(TECHNICIANS),
                random.choice(die_checks),
                due.strftime("%Y-%m-%d"),
            ))
            wid += 1

    orders.sort(key=lambda x: x[2])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["WO_ID", "Equipment_ID", "Created", "Priority", "Status", "Assigned_To", "Description", "Due_Date"])
        for o in orders:
            w.writerow(o)
    print(f"  work_orders.csv ({len(orders)} rows)")


if __name__ == "__main__":
    print("Generating PredMaCC Die/Stamping datasets...")
    write_equipment_master()
    failure_events = generate_failure_events()
    write_failure_events(failure_events)
    write_sensor_data(failure_events)
    write_maintenance_log(failure_events)
    write_work_orders(failure_events)
    print("Done.")
