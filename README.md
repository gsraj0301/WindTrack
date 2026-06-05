# 🌬️ WindTrack — Wind Farm IoT Dashboard

Proof of Concept for an IoT-powered wind turbine monitoring platform.

## Dashboards
- **Asset Dashboard** — 100 turbines, health scores, IoT status, map view
- **Power Generation** — Daily / Monthly / Yearly output analysis

## Tech Stack
Python · Streamlit · Plotly · Pandas · Synthetic Data (100 turbines, 2024)

## Run Locally
pip install -r requirements.txt
python scripts/generate_data.py
cd dashboard && streamlit run app.py

## Live Demo
[windtrack-raj.streamlit.app](https://windtrack-raj.streamlit.app)