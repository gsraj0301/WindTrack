<div align="center">
  <h1>🌬️ WindTrack</h1>
  <p><strong>IoT-Powered Wind Turbine Monitoring Dashboard</strong></p>
  <p>Proof of Concept — 100 turbines, real-time analytics, all synthetic data</p>
  <p>
    <a href="https://windtrack-raj.streamlit.app" target="_blank">
      <strong>🌐 Live Demo →</strong>
    </a>
  </p>
  <p>
    <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue" />
    <img alt="Streamlit" src="https://img.shields.io/badge/streamlit-1.30+-red" />
    <img alt="Plotly" src="https://img.shields.io/badge/plotly-5.18+-green" />
    <img alt="Pandas" src="https://img.shields.io/badge/pandas-2.0+-orange" />
  </p>
</div>

---

## 📖 The Story

India's wind energy capacity is growing fast — but monitoring hundreds of turbines spread across the country is a real challenge. Equipment failure, weather impact, and maintenance delays can cost millions.

I wanted to build something that shows what modern wind farm monitoring *could* look like. A single dashboard where you can see every turbine, its health, its power output, and whether it needs attention. No complex SCADA systems. No enterprise bloat. Just clean, interactive dashboards that give you the full picture at a glance.

This is a proof of concept — but the logic, the data modeling, and the visualizations are built to be production-realistic. 100 turbines, 5 states, 5 companies, 30-minute interval data for an entire year. Every turbine has a health score that degrades with age, realistic power output that accounts for weather and time of day, and IoT sensors that feed live readings.

WindTrack is my way of exploring what's possible with Python + Streamlit when you combine good data with good visuals.

---

## ✨ Features

### Asset Dashboard
- **Live KPIs** — total turbines, online/maintenance/offline counts, critical alerts, average health score
- **Smart filters** — filter by company, state, status, alert level, and IoT equipment
- **Interactive map** — all 100 turbines plotted across India, color-coded by status
- **Health monitoring** — histogram distribution and individual health progress bars
- **Data export** — download filtered turbine data as CSV

### Power Generation Dashboard
- **Farm-level KPIs** — total output (GWh), daily average, best turbine, top state and company
- **Daily view** — date range picker with per-turbine breakdown
- **Monthly view** — line chart, stacked bar by state, summary stats
- **Yearly summary** — top 10 / bottom 10 turbines, company comparison, full performance table
- **Turbine comparison** — select 2-6 turbines and compare monthly output side by side

### Data Engine
- **100 turbines** across 5 Indian states with realistic GPS coordinates
- **5 manufacturers** — Envision, Suzlon, Inox Wind, Vestas, GE Renewable
- **1.75M+ data points** — 30-minute interval power output for a full year
- **IoT simulation** — vibration, temperature, RPM, wind speed readings for equipped turbines
- **Realistic modeling** — health degrades with age, power varies by time/season/weather, maintenance affects output

---

## 🛠️ Tech Stack

| Layer              | Technology                         |
| ------------------ | ---------------------------------- |
| Language           | Python 3.12                        |
| Dashboard          | Streamlit 1.30+                    |
| Charts & Maps      | Plotly 5.18+                       |
| Data Processing    | Pandas 2.0+, NumPy 1.24+           |
| Synthetic Data     | Faker 20.0+                        |
| Deployment         | Streamlit Cloud                    |

---

## 📍 The Process

I wanted to explore the intersection of IoT data and interactive dashboards. Wind energy felt like the perfect use case — real-world relevance, geographic diversity, and interesting data patterns.

Started with a data generator that creates realistic turbine metadata. Every turbine has a company, location, install year, and health score. Then I modeled power output at 30-minute intervals for an entire year — accounting for time of day, seasonal wind patterns, and health-induced degradation. IoT sensors were added for a subset of turbines, with readings that degrade alongside turbine health.

The dashboards came next. Asset dashboard first — map, KPIs, filters, health scores. Then the power dashboard — daily, monthly, yearly views with comparison tools. Every chart is interactive, every filter actually does something.

The result is a POC that I'm genuinely proud of. It's not hooked up to real turbines (yet), but the architecture and visualization are production-ready. If a wind farm operator wanted something like this, they could take this and run with it.

---

## 🚀 Running Locally

```bash
pip install -r requirements.txt
python scripts/generate_data.py
cd dashboard && streamlit run app.py
```

---

<p align="center">
  Built with care by <strong>Raj G.</strong>
</p>
