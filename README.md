# PredMaCC

Predictive Maintenance Command Center for a **car door panel stamping press** — monitoring die health through 7 sensor channels, predicting failures, automating work orders, and tracking Overall Equipment Effectiveness (OEE).

Built with Streamlit and deployed to Snowflake (SiS).

## Problem

Manufacturers lose value to unplanned downtime because OT sensor data sits apart from ERP and maintenance context. PredMaCC converges IT and OT data to predict failures, support root cause investigation, and deliver a command center experience for alert triage and action.

## Die Sensors

| Sensor | Column | Nominal | What it monitors |
|---|---|---|---|
| Die Force | `Die_Force_kN` | ~850 kN | Stamping force per stroke |
| Die Temperature | `Die_Temperature_C` | ~45 C | Die surface thermal state |
| Cushion Pressure | `Cushion_Pressure_bar` | ~12 bar | Blank-holder hydraulic pressure |
| Die Strain | `Die_Strain_uE` | ~1200 uE | Micro-strain on die insert |
| Vibration | `Vibration_g` | ~0.8 g | Vibration RMS during press cycle |
| Ram Position | `Ram_Position_mm` | ~0 mm | Bottom-dead-center deviation |
| Proximity | `Proximity_mm` | ~2.5 mm | Punch-to-die clearance |

## Equipment (Dies)

| ID | Die | Type | Location |
|---|---|---|---|
| DIE-001 | Front-Left Door Panel | Progressive Die | Press Line 1 - Station A |
| DIE-002 | Front-Right Door Panel | Progressive Die | Press Line 1 - Station B |
| DIE-003 | Rear-Left Door Panel | Transfer Die | Press Line 2 - Station A |
| DIE-004 | Rear-Right Door Panel | Transfer Die | Press Line 2 - Station B |
| DIE-005 | Tailgate Inner Panel | Tandem Die | Press Line 3 - Station A |

## Dashboards (5 Pages)

1. **Command Center** — Active alert triage panel with severity indicators, die health scores, failure event timeline, work order summary
2. **Sensor Monitoring** — Time-series plots for all 7 sensors with warning/critical thresholds, anomaly highlighting, stroke count trend, sensor correlation heatmap
3. **Predictive Analytics** — Failure probability per die, root cause investigation with natural language summaries, contributing factor charts, remaining useful life estimates
4. **Work Orders** — Filterable work order table, priority/status distribution, technician workload, auto-generated WO suggestions from prediction engine
5. **OEE Dashboard** — Availability/Performance/Quality gauge charts, die-level OEE breakdown, downtime Pareto analysis, maintenance cost distribution

## Die Failure Modes

- Die Crack (fatigue from cyclic stamping load)
- Surface Galling (adhesive wear from sheet metal)
- Misalignment (guide pin wear)
- Thermal Distortion (uneven die temperature)
- Spring-back Defect (worn die profile)
- Slug Retention (ejection failure)
- Cushion Pressure Loss (hydraulic seal degradation)

## Project Structure

```
PredMaCC_sl/
├── streamlit_app.py              # Main entry point + global filters
├── pages/
│   ├── 1_Command_Center.py       # Alert triage, health scores, failure timeline
│   ├── 2_Sensor_Monitoring.py    # Sensor time-series, thresholds, correlation
│   ├── 3_Predictive_Analytics.py # Failure prediction, root cause, RUL
│   ├── 4_Work_Orders.py          # WO management, auto-suggestions
│   └── 5_OEE_Dashboard.py        # OEE gauges, Pareto, cost breakdown
├── utils/
│   ├── data_loader.py            # Cached loaders for all datasets
│   ├── analytics.py              # OEE, anomaly detection, failure prediction
│   └── alerts.py                 # Threshold-based alert generation
├── dataset/
│   ├── sensor_data.csv           # 5000 rows, 5 dies, 7 sensors
│   ├── equipment_master.csv      # 5 dies with type and criticality
│   ├── maintenance_log.csv       # Preventive + corrective records
│   ├── work_orders.csv           # Work orders with status/priority
│   └── failure_events.csv        # Historical failures with root causes
├── generate_data.py              # Dataset generator (correlated anomalies)
├── requirements.txt
└── snowflake.yml                 # SiS deployment manifest
```

## Running Locally

```bash
pip install -r requirements.txt
python generate_data.py           # generate/regenerate datasets
streamlit run streamlit_app.py
```

## Deployment

Deployed to **Streamlit in Snowflake (SiS)** using container runtime.

- Database/schema: `PREDMACC_DB.APP`
- App name: `PREDMACC_STREAMLIT`
- Compute pool: `SYSTEM_COMPUTE_POOL_CPU`
- Query warehouse: `COMPUTE_WH`

```bash
uvx --from snowflake-cli snow streamlit deploy --connection YRUZETZ-VG76067 --replace
```
