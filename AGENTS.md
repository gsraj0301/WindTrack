# WindTrack — Agent Memory

## Project
WindTrack is a synthetic wind turbine data generator and Streamlit monitoring dashboard. It creates CSV datasets for turbines, power output, and sensor readings.

## Project Structure
- `scripts/generate_data.py` — main data generation script
- `scripts/init_db.py` — loads CSVs into SQLite (`data/windtrack.db`)
- `scripts/simulator.py` — standalone live simulator (optional; not needed for the app)
- `dashboard/app.py` — Streamlit entry point (init DB, inline simulator thread, sidebar, routing)
- `dashboard/asset_dashboard.py` — asset overview page (turbine map, KPIs, filters, health scores)
- `dashboard/power_dashboard.py` — power generation dashboard (daily/monthly/yearly views, turbine comparison)
- `dashboard/ui.py` — shared UI primitives (CSS, status chips, KPI cards, header, plotly style)
- `data/` — contains generated CSVs + `windtrack.db` (`.gitignore`d)
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
- `px.scatter_mapbox` → `px.scatter_map` + `map_style` in `asset_dashboard.py` (plotly v7 removed mapbox traces)
- `plotly>=5.18.0` → `>=5.24.0` in `requirements.txt` (first version with `px.scatter_map`)
- `live_readings` query in `power_dashboard.py` dropped `state`/`health_score`/`status` (columns absent from `live_readings` schema → SQLite `no such column` crash)
- Simulator loop inlined into `dashboard/app.py` (Cloud can't run separate processes); guarded by `@st.cache_resource` so exactly one thread runs
- `use_container_width=True` → `width='stretch'` (deprecated in Streamlit; removal after 2025-12-31)
- Asset dashboard Reset filters: `pop()` keys → explicit `session_state[key] = "All"` assignment (Streamlit widgets ignore deleted keys; setting values is the documented approach)
- `st.segmented_control` has no `value` param — only `default` (TypeError if `value=` is used)

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

## Session 2026-09-08 — Live: Built Simpler Than the Railway Plan + UI Polish

The "Next Phase" plan above (FastAPI + Railway + HTTP) was **superseded**. The live demo was shipped with a
simpler stack that needs only Streamlit Cloud (free, no Railway/UptimeRobot):

### What was actually built
- **SQLite + inline simulator thread** instead of FastAPI:
  - `dashboard/app.py` starts one daemon thread (`@st.cache_resource`, so exactly one runs regardless of users)
  - The infinite loop is **inlined** in `app.py` (copied from `scripts/simulator.py`): every 10s writes 100 rows to
    `live_readings` and mutates 2-4 turbine statuses in `turbines`
  - "Starting..." until a cycle completes; sidebar shows last write + live reading count
- **Dashboards read SQLite directly** and auto-refresh via `st.fragment(run_every=15)`
- `ui.py` bug worth remembering: in `run_simulator`, `changes`/`now` must be initialized before the try so a
  failed cycle doesn't crash the thread (UnboundLocalError)

### UI polish (impeccable pass)
- **De-emoji**: headers, tabs, KPI labels, and nav are plain text; replaced emoji dots/badges with semantic
  tinted chips (`.wt_chip` / `.wt_dot` in `ui.py`)
- **Unified design system** in `dashboard/ui.py`: `kpi_card()`, `render_header()` (LIVE badge), `status/alert`
  chips, `style_fig()` (transparent bg, muted gridlines, Inter), one shared scoped CSS block
- **Live KPI deltas**: status/health counts show `▲ n / ▼ n vs last tick` computed from a `st.session_state`
  snapshot each fragment rerun
- **Filters**: Status/Alert use `st.segmented_control`; added Reset + active-filter summary + empty state
- **Caching perf fix**: `load_power()` (1.75M rows) and `load_turbines()` are `@st.cache_data(ttl=3600/60)` so
  the fragment only touches `live_readings` live — previous code re-read all rows every 15s
- **Sidebar**: replaced external icons8 logo with a CSS `.wt_logo` mark + compact SYSTEM STATUS block
  (Database / Simulator dots + meta)
- `use_container_width=True` → `width='stretch'` across all dashboards

### Current live URL
- `https://windtrack-j4l6fmrgkx5n8r9kodjgya.streamlit.app` (Streamlit Cloud; DB is ephemeral per deploy, re-seeds on first visit)

## Session 2026-09-10 — Sky.Light Theme + Global Footer + Health Delta Rounding

### Theme (dark → sky light)
- `.streamlit/config.toml`: `base="light"`, `primaryColor="#1E78B8"`, `backgroundColor="#D6E8F5"`,
  `secondaryBackgroundColor="#C2D9ED"`, `textColor="#0F2337"` (steel-blue-grey, kills near-white flashbang)
- `ui.py` tokens: `ok/warn/crit` → `#16A34A/#D97706/#DC2626` (readable on light); `ink`→`#0F2337`-family `#1A2332`,
  `muted`→`#5B6470`, `grid`→`rgba(26,35,50,0.08)`; `.wt_card` → white; `.wt_live` badge → blue `#1E78B8` + blue pulse;
  `.wt_logo` gradient → `#1E78B8→#155A8A`; hover labels → white
- Map: `map_style="carto-positron"` (light, no API key); font/title → `#1A2332`
- Accent series: `color_discrete_sequence=['#2E9E56']` → `['#1E78B8']` in asset hist + power monthly line
- Semantic status colors in charts/pies/KPIs kept as-is (only light-theme variants)

### Global footer
- Styled HTML footer via `.wt_footer` CSS in `ui.py` (centered, muted `#5B6470`, hairline top border)
- Rendered in `dashboard/app.py` after page routing — shows on all pages; sits outside the `run_every=15` fragments
- `st.set_page_config(..., footer=...)` does **NOT exist** in Streamlit (≤1.58.0) — TypeError on Cloud; use the HTML approach
- `requirements.txt` stays `streamlit>=1.30.0` (no version bump needed)
- This footer is the default for all of Raj's projects (see README_MAKER structure step 8)

### Health delta rounding
- `asset_dashboard.py` avg-health delta: `round(d, 1)` so it shows `-0.7 pts vs last tick` instead of a long float
- Other deltas are integer counts (online/maintenance/offline/critical) or already rounded (power GWh round 2) — no change

### Filter reset fix
- Reset button didn't visually reset Status, Alert Level, Company, State filters back to "All"
- Root cause: `st.session_state.pop()` deletes keys but Streamlit widgets ignore deleted keys on re-render
- Fix: set explicit values (`st.session_state['asset_status'] = "All"`) instead of popping — Streamlit reads these before widget creation
- `st.segmented_control` uses `default` not `value` — `value=` causes TypeError
