"""Generate PredMaCC datasets for car door panel stamping press dies.

Sensor data is hourly for ~42 days per die. Each failure has a failure-mode specific
sensor signature that ramps up over the 48 hours before the failure, so pre-failure
behaviour in the sensor data explains the failure recorded in the ERP-style tables.
"""

import csv
import datetime
import math
import os
import random

random.seed(42)

BASE = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

START = datetime.datetime(2024, 1, 1, 0, 0, 0)
N_HOURS = 1000
END = START + datetime.timedelta(hours=N_HOURS)
RAMP_HOURS = 48

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

NOMINAL = {"force": 850.0, "temp": 45.0, "pressure": 12.0, "strain": 1200.0, "vib": 0.8, "position": 0.0, "prox": 2.5}
NOISE = {"force": 6.0, "temp": 0.4, "pressure": 0.08, "strain": 15.0, "vib": 0.04, "position": 0.02, "prox": 0.03}
REVERT = 0.2

# Sensor shift (at full degradation) that precedes each failure mode
SIGNATURE = {
    "Die Crack": {"strain": 450, "vib": 1.3, "force": 40},
    "Surface Galling": {"force": 90, "vib": 0.9, "temp": 12},
    "Misalignment": {"position": 0.9, "prox": -1.2, "vib": 0.8},
    "Thermal Distortion": {"temp": 28, "strain": 250, "prox": -0.6},
    "Spring-back Defect": {"force": -120, "position": -0.7, "strain": -150},
    "Slug Retention": {"prox": 1.8, "force": 110, "vib": 0.6},
    "Cushion Pressure Loss": {"pressure": -3.8, "force": -60, "position": 0.4},
}

# (die, failure mode, hours after data window end) - degradations in progress at "now"
PENDING = [
    ("DIE-002", "Die Crack", 3),
    ("DIE-004", "Thermal Distortion", 5),
]

WARN = {
    "force": (700, 1000), "temp": (None, 60), "pressure": (9.5, 15), "strain": (None, 1500),
    "vib": (None, 2.0), "prox": (1.2, 3.8),
}


def _open(path):
    return open(path, "w", newline="", encoding="utf-8")


def write_equipment_master():
    with _open(os.path.join(DATASET_DIR, "equipment_master.csv")) as f:
        w = csv.writer(f)
        w.writerow(["Equipment_ID", "Name", "Type", "Location", "Install_Date", "Criticality"])
        w.writerows(EQUIPMENT)
    print(f"  equipment_master.csv ({len(EQUIPMENT)} rows)")


def generate_failure_events():
    events, eid = [], 1
    for eq_id, *_ in EQUIPMENT:
        offsets = []
        for _ in range(random.randint(3, 5)):
            for _ in range(50):
                off = random.randint(60, N_HOURS - 60)
                if all(abs(off - o) >= 96 for o in offsets):
                    offsets.append(off)
                    break
        for off in sorted(offsets):
            mode, cause = random.choice(FAILURE_MODES)
            events.append((f"FE-{eid:04d}", eq_id, START + datetime.timedelta(hours=off), mode, cause, round(random.uniform(2, 24), 1)))
            eid += 1
    events.sort(key=lambda x: x[2])
    return events


def write_failure_events(events):
    with _open(os.path.join(DATASET_DIR, "failure_events.csv")) as f:
        w = csv.writer(f)
        w.writerow(["Event_ID", "Equipment_ID", "Timestamp", "Failure_Mode", "Root_Cause", "Downtime_hrs"])
        for e in events:
            w.writerow([e[0], e[1], e[2].strftime("%Y-%m-%d %H:%M:%S"), e[3], e[4], e[5]])
    print(f"  failure_events.csv ({len(events)} rows)")


def _is_anomaly(v):
    for key, (lo, hi) in WARN.items():
        if lo is not None and v[key] < lo:
            return 1
        if hi is not None and v[key] > hi:
            return 1
    return 1 if abs(v["position"]) > 0.8 else 0


def write_sensor_data(events):
    by_die = {}
    for _, eq_id, ts, mode, _, downtime in events:
        by_die.setdefault(eq_id, []).append((ts, mode, downtime))
    # Developing degradations: failure expected shortly after the data window ends (not yet in failure_events)
    for eq_id, mode, hrs_after_end in PENDING:
        by_die.setdefault(eq_id, []).append((END + datetime.timedelta(hours=hrs_after_end), mode, 0))

    rows = 0
    with _open(os.path.join(DATASET_DIR, "sensor_data.csv")) as f:
        w = csv.writer(f)
        w.writerow([
            "Timestamp", "Equipment_ID", "Stroke_Count", "Die_Force_kN", "Die_Temperature_C",
            "Cushion_Pressure_bar", "Die_Strain_uE", "Vibration_g", "Ram_Position_mm", "Proximity_mm",
            "Is_Anomaly",
        ])
        for eq_id, *_ in EQUIPMENT:
            fails = by_die.get(eq_id, [])
            v = dict(NOMINAL)
            stroke = 0
            for i in range(N_HOURS):
                ts = START + datetime.timedelta(hours=i)

                down = any(ft <= ts < ft + datetime.timedelta(hours=dt) for ft, _, dt in fails)
                ramp, shift = 0.0, {}
                for ft, mode, _ in fails:
                    hrs = (ft - ts).total_seconds() / 3600
                    if 0 < hrs <= RAMP_HOURS:
                        ramp = 1 - hrs / RAMP_HOURS
                        shift = SIGNATURE[mode]

                diurnal = 5.0 * math.sin(2 * math.pi * (ts.hour - 6) / 24)
                if down:
                    v = dict(NOMINAL)
                else:
                    for k in v:
                        target = NOMINAL[k] + shift.get(k, 0) * ramp + (diurnal if k == "temp" else 0)
                        v[k] += REVERT * (target - v[k]) + random.gauss(0, NOISE[k])

                if not down:
                    stroke += int(random.randint(540, 600) * (1 - 0.3 * ramp))

                w.writerow([
                    ts.strftime("%Y-%m-%d %H:%M:%S"), eq_id, stroke,
                    round(v["force"], 1), round(v["temp"], 2), round(v["pressure"], 2),
                    round(v["strain"], 1), round(v["vib"], 3), round(v["position"], 3), round(v["prox"], 3),
                    0 if down else _is_anomaly(v),
                ])
                rows += 1
    print(f"  sensor_data.csv ({rows} rows)")


def write_maintenance_log(events):
    tasks = [
        "Die surface polishing and inspection",
        "Guide pin and bushing clearance check",
        "Hydraulic cushion pressure calibration",
        "Die alignment and shim adjustment",
        "Proximity sensor calibration",
        "Strain gauge zero-drift recalibration",
    ]
    records, mid = [], 1
    for eq_id, *_ in EQUIPMENT:
        d = START + datetime.timedelta(days=random.randint(2, 8))
        while d < END:
            records.append((f"MNT-{mid:04d}", eq_id, d.strftime("%Y-%m-%d"), "Preventive", random.choice(tasks),
                            round(random.uniform(2, 8), 1), round(random.uniform(5000, 25000), 2)))
            mid += 1
            d += datetime.timedelta(days=random.randint(7, 14))

    for _, eq_id, ts, mode, cause, downtime in events:
        mtype = random.choice(["Corrective", "Breakdown"])
        records.append((f"MNT-{mid:04d}", eq_id, ts.strftime("%Y-%m-%d"), mtype, f"{mtype} repair: {mode} - {cause}",
                        round(downtime + random.uniform(1, 8), 1), round(random.uniform(15000, 120000), 2)))
        mid += 1

    records.sort(key=lambda x: x[2])
    with _open(os.path.join(DATASET_DIR, "maintenance_log.csv")) as f:
        w = csv.writer(f)
        w.writerow(["Maintenance_ID", "Equipment_ID", "Date", "Type", "Description", "Duration_hrs", "Cost_INR"])
        w.writerows(records)
    print(f"  maintenance_log.csv ({len(records)} rows)")


def _status(created):
    age_days = (END - created).days
    if age_days > 10:
        return random.choices(["Completed", "Overdue", "In Progress"], weights=[70, 20, 10])[0]
    return random.choices(["Open", "In Progress", "Completed"], weights=[40, 40, 20])[0]


def write_work_orders(events):
    priorities = ["Low", "Medium", "High", "Critical"]
    checks = [
        "Scheduled die tryout and panel quality audit",
        "Die clearance measurement and adjustment",
        "Blank-holder pressure rebalancing",
        "Proximity sensor functional test",
        "Die temperature sensor validation",
    ]
    orders, wid = [], 1
    for _, eq_id, ts, mode, cause, _ in events:
        created = ts - datetime.timedelta(hours=random.randint(1, 12))
        due = created + datetime.timedelta(days=random.randint(1, 5))
        orders.append((f"WO-{wid:04d}", eq_id, created.strftime("%Y-%m-%d %H:%M:%S"),
                       random.choices(priorities, weights=[1, 2, 4, 3])[0], _status(created),
                       random.choice(TECHNICIANS), f"Investigate {mode}: {cause}", due.strftime("%Y-%m-%d")))
        wid += 1

    for eq_id, *_ in EQUIPMENT:
        for _ in range(random.randint(4, 8)):
            created = START + datetime.timedelta(hours=random.randint(0, N_HOURS - 24))
            due = created + datetime.timedelta(days=random.randint(3, 14))
            orders.append((f"WO-{wid:04d}", eq_id, created.strftime("%Y-%m-%d %H:%M:%S"),
                           random.choice(["Low", "Medium"]), _status(created), random.choice(TECHNICIANS),
                           random.choice(checks), due.strftime("%Y-%m-%d")))
            wid += 1

    orders.sort(key=lambda x: x[2])
    with _open(os.path.join(DATASET_DIR, "work_orders.csv")) as f:
        w = csv.writer(f)
        w.writerow(["WO_ID", "Equipment_ID", "Created", "Priority", "Status", "Assigned_To", "Description", "Due_Date"])
        w.writerows(orders)
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
