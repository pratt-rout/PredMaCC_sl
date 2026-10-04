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


## AI Assistant (Cortex Agents)

Page 6 talks to three **Cortex Agent objects** in `PREDMACC_DB.APP`, called with `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` (multi-turn via Cortex threads).

| Agent | Tools | Answers |
|---|---|---|
| `DIE_HEALTH_ANALYST` | Cortex Analyst on `DIE_MAINTENANCE_SV`, data-to-chart | Downtime, failures, anomaly rates, maintenance cost, work orders; draws charts |
| `ROOT_CAUSE_INVESTIGATOR` | Cortex Analyst + `GET_PRE_FAILURE_PROFILE` procedure | Why a die failed or is drifting, from pre-failure sensor shifts in standard deviations |
| `MAINTENANCE_KNOWLEDGE_AGENT` | Cortex Search `MAINTENANCE_KB_SEARCH` | SOP / manual questions, with sources |

Supporting objects: tables `SENSOR_DATA`, `EQUIPMENT_MASTER`, `FAILURE_EVENTS`, `MAINTENANCE_LOG`, `WORK_ORDERS`, `KNOWLEDGE_CHUNKS`; semantic view `DIE_MAINTENANCE_SV`; stage `DATA_STAGE`.

Code: `agents/base.py` (one `Agent` class + response parsing) and one small file per agent holding its agent name and starter questions. To add an agent: create it in Snowflake, add a file in `agents/`, register it in `agents/__init__.py`.

The SOPs in `knowledge/` are **sample placeholders**. The sensor data is synthetic: each failure mode has a sensor signature that ramps up over the 48 hours before the failure, and DIE-002 / DIE-004 have faults developing at the end of the data window.

### Refreshing data and documents

```bash
python generate_data.py            # regenerate CSVs (then re-upload with snow stage copy + COPY INTO)
python scripts/load_knowledge.py   # re-chunk knowledge/ and reload KNOWLEDGE_CHUNKS (search index refreshes itself)
```

### Required privileges for the app's owner role

`SNOWFLAKE.CORTEX_AGENT_USER` database role, `USAGE` on the three agents, `SELECT` on the tables, `USAGE` on the semantic view, search service and procedure, and `USAGE` on `COMPUTE_WH`.

The dashboards read the local CSVs. The AI Assistant page needs a Snowflake connection.

## Deployment

Deployed to **Streamlit in Snowflake (SiS)** using container runtime.

- Database/schema: `PREDMACC_DB.APP`
- App name: `PREDMACC_STREAMLIT`
- Compute pool: `SYSTEM_COMPUTE_POOL_CPU`
- Query warehouse: `COMPUTE_WH`

