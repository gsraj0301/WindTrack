# WindTrack — Agent Memory

## Project
WindTrack is a synthetic wind turbine data generator. It creates CSV datasets for turbines, power output, and sensor readings.

## Project Structure
- `main.py` — placeholder entry point (prints "Hello from windtrack!")
- `scripts/generate_data.py` — main data generation script
- `dashboard/app.py` — empty (Streamlit dashboard placeholder)
- `dashboard/asset_dashboard.py` — empty (Streamlit dashboard placeholder)
- `data/` — contains generated CSVs (`.gitignore`d)

## Config
- Python 3.12 (`uv` package manager)
- Dependencies in `pyproject.toml`: faker, numpy, pandas, plotly, streamlit
- `requirements.txt` also present (note: has `plotify` typo instead of `plotly`)
- `.gitignore` excludes `data/*.csv`

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

## Output
Generated CSVs land in `data/`:
- `turbines.csv`
- `power_output.csv`
- `sensor_readings.csv`
