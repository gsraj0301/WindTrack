# WindTrack — Agent Memory

## Project
WindTrack is a synthetic wind turbine data generator and Streamlit monitoring dashboard. It creates CSV datasets for turbines, power output, and sensor readings.

## Project Structure
- `scripts/generate_data.py` — main data generation script
- `dashboard/app.py` — Streamlit multi-page entry point (routes to asset/power pages)
- `dashboard/asset_dashboard.py` — asset overview page (turbine map, KPIs, filters, health scores)
- `dashboard/power_dashboard.py` — power generation dashboard (daily/monthly/yearly views, turbine comparison)
- `data/` — contains generated CSVs (`.gitignore`d)
- `.streamlit/config.toml` — dark theme and headless server config
- `requirements.txt` — pinned dependencies

## Config
- Python 3.12 (`uv` package manager)
- Dependencies in `requirements.txt`: pandas, numpy, faker, streamlit, plotly
- `.gitignore` excludes `data/*.csv`
- Streamlit Cloud entry point: `dashboard/app.py`

## Scripts
- `scripts/generate_data.py` — generates `turbines.csv`, `power_output.csv`, `sensor_readings.csv`

## Key Fixes Applied
- `kl=1` → `k=1` in `random.choices()` (crash bug)
- `Suzion` → `Suzlon`
- `Maharastra` → `Maharashtra`
- `Maintainance` → `Maintenance`
- `TURBNINE` → `TURBINE` (comment typo)
- `Comfig` → `Config` (comment typo)
- `install_year` range: `(2010, 2023)` → `(2015, 2023)`
- `iot_probability` for young turbines: `0.05` → `0.85`
- `date_range` freq in power output: `'h'` → `'30min'`
- `iot_probability` for old turbines: `0.202` → `0.20`
- `plotify` → `plotly` in `asset_dashboard.py` import and `requirements.txt`
- `filtered`/`filtered_df` variable name mismatch in `asset_dashboard.py`
- Created missing `power_dashboard.py` (referenced by `app.py` import)
- Removed `pyproject.toml` and `uv.lock` (conflicted with `requirements.txt` on Streamlit Cloud)
- Switched all file path resolution to `os.path.abspath(__file__)` for reliable Streamlit Cloud deployment
- Pinned exact dependency versions in `requirements.txt`

## Output
Generated CSVs land in `data/`:
- `turbines.csv`
- `power_output.csv`
- `sensor_readings.csv`

## Deployment (Streamlit Cloud)
- Main file path: `dashboard/app.py`
- Uses `requirements.txt` (not pyproject.toml)

## Session 2026-06-22 — Next Phase: Live Pipeline (NOT YET BUILT)

### Goal
Turn WindTrack from a static-CSV dashboard into a live pipeline demo: simulated sensor data → FastAPI ingestion → SQLite → auto-refreshing dashboard. Single URL for uncle to show investors.

### Architecture Decision (approved, not yet built)
```
Streamlit Cloud (dashboard, free, no CC)
   └── reads from Railway/FastAPI via HTTP (every 10s)
         └── Railway (free, no CC): FastAPI + SQLite + background simulator
               └── SQLite: 3 tables (turbines, power_output, sensor_readings)
UptimeRobot: pings both URLs every 5 min to prevent sleep
```

### Why this split
- Streamlit Cloud can't run FastAPI or persistent background processes (read-only fs)
- Railway doesn't require a credit card (free tier: $5 trial + $1/mo credit)
- Uncle gets one URL to share (Streamlit Cloud URL)
- UptimeRobot keeps both awake for free

### The 5-Step Plan (approved, not yet built)

**Step 1 — Live Simulator** (`scripts/simulator.py`, NEW)
- Reads turbine metadata from existing `turbines.csv`
- Every 10s picks a random turbine, generates kwh + sensor readings (same logic as generate_data.py)
- POSTs JSON to FastAPI's `/api/sensor-data`
- Responds to `turbine_id` validation (404 if unknown)

**Step 2 — SQLite Storage** (`api/database.py`, NEW)
- Tables: turbines, power_output, sensor_readings
- On startup: seed from existing CSVs if DB empty; WAL mode for concurrent access
- Dashboard reads via HTTP from FastAPI (not direct SQLite)

**Step 3 — FastAPI Ingestion Endpoint** (`api/main.py`, NEW)
- `POST /api/sensor-data` — the plug point for real hardware (ESP32/SCADA)
- `GET /api/turbines` — returns turbine list
- `GET /api/power?turbine_id=&since=` — power data with filters
- `GET /api/sensors/latest` — latest sensor reading per turbine

**Step 4 — Dashboard Auto-Refresh** (modify `dashboard/asset_dashboard.py`, `dashboard/power_dashboard.py`)
- Replace `pd.read_csv()` with HTTP calls to FastAPI
- Use `st.fragment(run_every=10)` for live tick
- Dashboard visibly updates every 10 seconds

**Step 5 — Technical Note in README** (modify `README.md`)
- "How This Becomes Real" section: architecture diagram, API contract, curl example
- "Zero dashboard changes" claim for real hardware connection
- SQLite → TimescaleDB upgrade path

### Deployment Plan
- Streamlit Cloud: already deployed at `https://windtrack-raj.streamlit.app`
- Railway: sign up (no CC), deploy Docker container with FastAPI + simulator
- Dockerfile: supervisord runs 3 processes (FastAPI:8000, simulator:bg, health check)
- UptimeRobot: free monitors on both URLs, 5-min intervals

### Files to Create/Modify (not yet done)
| File | Action |
|---|---|
| `api/main.py` | NEW — FastAPI app |
| `api/database.py` | NEW — SQLite setup + seed |
| `api/__init__.py` | NEW — empty |
| `scripts/simulator.py` | NEW — live data generator |
| `dashboard/asset_dashboard.py` | MODIFY — HTTP reads + auto-refresh |
| `dashboard/power_dashboard.py` | MODIFY — HTTP reads + auto-refresh |
| `dashboard/app.py` | MODIFY — env detection (live vs CSV mode) |
| `requirements.txt` | MODIFY — add fastapi, uvicorn, httpx |
| `Dockerfile` | NEW — multi-stage, supervisord |
| `README.md` | MODIFY — add "How This Becomes Real" section |

### Constraint
- No credit card — must use free tiers only
- Railway (no CC) for FastAPI + SQLite + simulator
- UptimeRobot (free) to keep both platforms awake
