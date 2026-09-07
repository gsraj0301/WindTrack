import streamlit as st
import os
import sys
import sqlite3
import threading
import pandas as pd

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
from simulator import simulator_loop

if not os.path.exists(db_path):
    with st.spinner("Initializing database..."):
        init_database()
    st.success("Database initialized!")
    st.rerun()

# ── Start embedded simulator thread ───────────────────────────────
# @st.cache_resource is shared across ALL connected sessions in the
# process, so exactly one simulator thread runs regardless of how many
# people are viewing the app. A st.session_state guard would not work
# here (it is per-browser-session and would spawn duplicate threads).
@st.cache_resource
def _start_simulator_thread():
    t = threading.Thread(target=simulator_loop, daemon=True, name="windtrack-simulator")
    t.start()
    return t

_start_simulator_thread()

# Sidebar Navigation
st.sidebar.image(
    "https://img.icons8.com/fluency/96/wind-turbine.png",
    width=80
)

st.sidebar.title("WindTrack")
st.sidebar.caption("Wind Farm Intelligence Platform")

# ── Sidebar status section ────────────────────────────────────────
st.sidebar.markdown("---")
if os.path.exists(db_path):
    st.sidebar.caption("🟢 Database: Connected")
    try:
        conn = sqlite3.connect(db_path)
        last_write = pd.read_sql_query(
            "SELECT MAX(timestamp) as ts FROM live_readings", conn
        ).iloc[0]['ts']
        live_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM live_readings", conn
        ).iloc[0]['cnt']
        conn.close()
        st.sidebar.caption(f"Last simulator write: {last_write or 'None yet'}")
        st.sidebar.caption(f"Live readings: {live_count:,}")
    except Exception:
        st.sidebar.caption("Database: Error")
else:
    st.sidebar.caption("🔴 Database: Not Found")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
     ["🏭  Asset Dashboard", "⚡  Power Generation"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("PoC · 100 Turbines · India")
st.sidebar.caption("Data Year: 2024")

# ── Route to page ───────────────────────────────────────
if page == "🏭  Asset Dashboard":
    from asset_dashboard import show
    show()
else:
    from power_dashboard import show
    show()