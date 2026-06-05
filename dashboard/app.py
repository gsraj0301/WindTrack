import streamlit as st

st.set_page_config(
    page_title="WindTrack",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar Navigation
st.sidebar.image(
    "https://img.icons8.com/fluency/96/wind-turbine.png",
    width=80
)

st.sidebar.title("WindTrack")
st.sidebar.caption("Wind Farm Intelligence Platform")
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