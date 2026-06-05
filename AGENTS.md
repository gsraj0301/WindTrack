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
