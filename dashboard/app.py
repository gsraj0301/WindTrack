import streamlit as st
import os
import sys
import sqlite3
import threading
import random
import time
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="WindTrack",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────
base = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base, '..', 'data', 'windtrack.db')
scripts_dir = os.path.join(base, '..', 'scripts')
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# ── Auto-init database if not exists ──────────────────────────────
from init_db import init_database

if not os.path.exists(db_path):
    with st.spinner("Initializing database..."):
        init_database()
    st.success("Database initialized!")
    st.rerun()

# ── Inline simulator logic ────────────────────────────────────────
# The loop below is inlined (rather than importing scripts/simulator.py)
# so the app runs the live simulator without a separate process — it works
# on Streamlit Cloud, which cannot run persistent background processes.
CYCLE_SECONDS = 10

STATUS_TRANSITIONS = {
    'Online':    {'Warning': 0.10},
    'Warning':   {'Critical': 0.20, 'Online': 0.30},
    'Critical':  {'Warning': 0.15},
}

HEALTH_RANGES = {
    'Online':   (75, 85),
    'Warning':  (50, 65),
    'Critical': (30, 49),
}

ALERT_MAP = {'Online': 'Normal', 'Warning': 'Warning', 'Critical': 'Critical'}


def get_readings(turbines):
    """Generate one reading per turbine."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rows = []
    for t in turbines:
        tid, cap, health, status = t[0], t[1], t[2], t[3]
        h_frac = health / 100.0
        kwh = cap * random.uniform(0.15, 0.40) * h_frac * random.uniform(0.85, 1.15)
        if status == 'Offline':
            kwh = 0.0
        elif status == 'Maintenance':
            kwh *= random.uniform(0.0, 0.3)

        vibration = max(random.uniform(0.1, 3.5) * (2 - h_frac) + random.gauss(0, 0.1), 0.1)
        temp = np.clip(random.uniform(35, 95) + (1 - h_frac) * 30 + random.gauss(0, 1.5), 30, 110)
        rpm = round(max(random.uniform(0, 18) * h_frac + random.gauss(0, 0.5), 0), 1) if status != 'Offline' else 0.0
        wind = max(random.uniform(3, 15) + random.gauss(0, 1), 0)

        rows.append((
            tid,
            now,
            round(vibration, 3),
            round(float(temp), 1),
            rpm,
            round(wind, 1),
            round(max(kwh, 0), 2),
            float(health),
            status,
            ALERT_MAP.get(status, 'Normal')
        ))
    return rows, now


def mutate_statuses(cursor, turbines):
    """Pick 2-4 random turbines and possibly shift their status."""
    changes = []
    sample = random.sample(turbines, min(random.randint(2, 4), len(turbines)))
    for t in sample:
        tid, _cap, _health, status = t[0], t[1], t[2], t[3]
        transitions = STATUS_TRANSITIONS.get(status, {})
        for new_status, prob in transitions.items():
            if random.random() < prob:
                new_health = random.randint(*HEALTH_RANGES[new_status])
                new_alert = ALERT_MAP[new_status]
                cursor.execute(
                    "UPDATE turbines SET health_score=?, status=?, alert_level=? WHERE turbine_id=?",
                    (new_health, new_status, new_alert, tid)
                )
                changes.append(f"{tid}: {status}→{new_status}")
                break
    return changes


def run_cycle(conn, cycle_num=0):
    """Run one simulator cycle against an open connection.

    Returns (now, num_rows, changes) where changes is a list of status-change strings.
    Caller is responsible for committing.
    """
    cursor = conn.cursor()
    turbines = cursor.execute(
        "SELECT turbine_id, capacity_kw, health_score, status FROM turbines"
    ).fetchall()

    rows, now = get_readings(turbines)
    cursor.executemany(
        "INSERT INTO live_readings (turbine_id, timestamp, vibration_g, temp_c, rpm, wind_speed_ms, kwh, health_score, status, alert_level) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows
    )

    changes = mutate_statuses(cursor, turbines)
    return now, len(rows), changes


def run_simulator():
    """Infinite loop, run as a background daemon thread."""
    cycle = 0
    while True:
        cycle += 1
        changes = []
        now = num_rows = None
        conn = sqlite3.connect(db_path, timeout=10)
        try:
            now, num_rows, changes = run_cycle(conn, cycle)
            conn.commit()
        except Exception as e:
            print(f"  Cycle {cycle:>4} | ERROR: {e}")
            conn.rollback()
        finally:
            conn.close()

        change_str = " | ".join(changes) if changes else "none"
        print(f"  Cycle {cycle:>4} | {now} | {num_rows} rows | Status changes: {change_str}")
        time.sleep(CYCLE_SECONDS)


# ── Start embedded simulator thread ───────────────────────────────
# @st.cache_resource is shared across ALL connected sessions in the
# process, so exactly one simulator thread runs regardless of how many
# people are viewing the app. A st.session_state guard would not work
# here (it is per-browser-session and would spawn duplicate threads).
@st.cache_resource
def _start_simulator_thread():
    t = threading.Thread(target=run_simulator, daemon=True, name="windtrack-simulator")
    t.start()
    return t

_sim_thread = _start_simulator_thread()

# Shared styles (sidebar needs the same tokens as the pages)
from ui import inject_css
inject_css()

# Sidebar Navigation
st.sidebar.markdown(
    "<style>.wt_logo{width:44px;height:44px;border-radius:11px;"
    "background:linear-gradient(140deg,#2E9E56,#1D6B38);display:flex;align-items:center;"
    "justify-content:center;color:#fff;font-size:22px;font-weight:800;}</style>",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<div style='display:flex;align-items:center;gap:12px'>"
    "<span class='wt_logo'>W</span>"
    "<div>"
    "<div style='font-size:19px;font-weight:700;color:#FAFAFA'>WindTrack</div>"
    "<div style='font-size:12px;color:#8B93A7'>Wind Farm Intelligence Platform</div>"
    "</div></div>",
    unsafe_allow_html=True,
)

# ── Sidebar status section ────────────────────────────────────────
st.sidebar.markdown("---")
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        last_write = pd.read_sql_query(
            "SELECT MAX(timestamp) as ts FROM live_readings", conn
        ).iloc[0]['ts']
        live_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM live_readings", conn
        ).iloc[0]['cnt']
        conn.close()
        db_tone = 'ok'
        db_label = "Database &middot; Connected"
    except Exception:
        db_tone = 'crit'
        db_label = "Database &middot; Error"
        last_write = None
        live_count = 0
else:
    db_tone = 'crit'
    db_label = "Database &middot; Not Found"
    last_write = None
    live_count = 0

sim_tone = 'ok' if _sim_thread.is_alive() else 'warn'
sim_label = ("Simulator &middot; Running" if _sim_thread.is_alive()
             else "Simulator &middot; Starting")

st.sidebar.markdown(
    f"<div class='wt_sys'>"
    f"<div style='font-size:12px;font-weight:700;letter-spacing:0.08em;color:#8B93A7'>SYSTEM STATUS</div>"
    f"<div class='wt_sysrow'><span class='wt_dot {db_tone}'></span>{db_label}</div>"
    f"<div class='wt_sysrow'><span class='wt_dot {sim_tone}'></span>{sim_label}</div>"
    f"<div class='wt_meta'>Last write: {last_write or 'None yet'}<br>Live readings: {live_count:,}</div>"
    f"</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Asset Dashboard", "Power Generation"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("PoC · 100 Turbines · India")
st.sidebar.caption("Data Year: 2024")

# ── Route to page ───────────────────────────────────────
if page == "Asset Dashboard":
    from asset_dashboard import show
    show()
else:
    from power_dashboard import show
    show()