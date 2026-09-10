import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sqlite3

from ui import (
    inject_css, style_fig, kpi_card,
    render_header, render_legend,
)

COLORS = {'ok': '#16A34A', 'warn': '#D97706', 'crit': '#DC2626'}


@st.cache_data(ttl=60, show_spinner=False)
def load_turbines():
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, '..', 'data', 'windtrack.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM turbines", conn)
    conn.close()
    return df


def compute_kpis(df):
    return {
        'total':     len(df),
        'online':    int((df['status'] == 'Online').sum()),
        'maintenance': int((df['status'] == 'Maintenance').sum()),
        'offline':   int((df['status'] == 'Offline').sum()),
        'iot':       int((df['iot_equipped'] == True).sum()),
        'critical':  int((df['alert_level'] == 'Critical').sum()),
        'health':    round(df['health_score'].mean(), 1),
    }


def fill_deltas(kpis):
    prev = st.session_state.get('_asset_snapshot')
    st.session_state['_asset_snapshot'] = kpis
    if prev is None:
        return {k: None for k in kpis}
    return {k: kpis[k] - prev[k] for k in kpis}


@st.fragment(run_every=15)
def show():
    inject_css()
    if st.session_state.pop('_reset_filters', False):
        st.session_state['asset_company'] = "All"
        st.session_state['asset_state'] = "All"
        st.session_state['asset_status'] = "All"
        st.session_state['asset_alert'] = "All"
        st.session_state['asset_iot'] = False
    df = load_turbines()
    kpis = compute_kpis(df)
    deltas = fill_deltas(kpis)

    render_header(
        "Asset Overview",
        "Fleet-wide status, health, and turbine locations across the farm network.",
        live=True,
    )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── KPI row ─────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    with k1:
        st.markdown(kpi_card("Total Turbines", kpis['total']), unsafe_allow_html=True)
    with k2:
        d = deltas['online']
        sub = f"▲ {d} vs last tick" if d and d > 0 else (f"▼ {abs(d)} vs last tick" if d and d < 0 else "")
        st.markdown(kpi_card("Online", kpis['online'], sub,
                             value_color=COLORS['ok']), unsafe_allow_html=True)
    with k3:
        d = deltas['maintenance']
        sub = f"▲ {d} vs last tick" if d and d > 0 else (f"▼ {abs(d)} vs last tick" if d and d < 0 else "")
        st.markdown(kpi_card("Maintenance", kpis['maintenance'], sub,
                             value_color=COLORS['warn']), unsafe_allow_html=True)
    with k4:
        d = deltas['offline']
        sub = f"▲ {d} vs last tick" if d and d > 0 else (f"▼ {abs(d)} vs last tick" if d and d < 0 else "")
        st.markdown(kpi_card("Offline", kpis['offline'], sub,
                             value_color=COLORS['crit']), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_card("IoT Equipped", kpis['iot'], "turbines with live sensors"),
                    unsafe_allow_html=True)
    with k6:
        d = deltas['critical']
        sub = f"▲ {d} vs last tick" if d and d > 0 else (f"▼ {abs(d)} vs last tick" if d and d < 0 else "")
        st.markdown(kpi_card("Critical Alerts", kpis['critical'], sub,
                             value_color=COLORS['crit'] if kpis['critical'] else COLORS['ok']),
                    unsafe_allow_html=True)
    with k7:
        d = deltas['health']
        sub = ""
        if d is not None and d != 0:
            sign = "+" if d > 0 else ""
            sub = f"{sign}{round(d, 1)} pts vs last tick"
        health_color = COLORS['ok'] if kpis['health'] >= 60 else COLORS['warn']
        st.markdown(kpi_card("Avg Health Score", f"{kpis['health']}%",
                             sub, value_color=health_color),
                    unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Filters ─────────────────────────────────────────────────
    st.markdown("#### Filters")
    f1, f2 = st.columns(2)
    with f1:
        companies = ["All"] + sorted(df['company'].unique().tolist())
        sel_company = st.selectbox("Company", companies, key="asset_company")
    with f2:
        states = ["All"] + sorted(df['state'].unique().tolist())
        sel_state = st.selectbox("State", states, key="asset_state")

    s1, s2 = st.columns(2)
    with s1:
        sel_status = st.segmented_control(
            "Status", ["All", "Online", "Maintenance", "Offline"],
            value="All", key="asset_status")
    with s2:
        sel_alert = st.segmented_control(
            "Alert Level", ["All", "Normal", "Warning", "Critical"],
            value="All", key="asset_alert")

    c1, c2 = st.columns([3, 1])
    with c1:
        iot_filter = st.checkbox("Only IoT-equipped turbines", key="asset_iot")
    with c2:
        if st.button("Reset filters", width='stretch'):
            st.session_state['_reset_filters'] = True
            st.rerun()

    # Apply filters
    filtered = df.copy()
    if sel_company != "All":
        filtered = filtered[filtered['company'] == sel_company]
    if sel_state != "All":
        filtered = filtered[filtered['state'] == sel_state]
    if (sel_status or "All") != "All":
        filtered = filtered[filtered['status'] == sel_status]
    if (sel_alert or "All") != "All":
        filtered = filtered[filtered['alert_level'] == sel_alert]
    if iot_filter:
        filtered = filtered[filtered['iot_equipped'] == True]

    active = []
    if sel_company != "All":
        active.append(f"Company = {sel_company}")
    if sel_state != "All":
        active.append(f"State = {sel_state}")
    if (sel_status or "All") != "All":
        active.append(f"Status = {sel_status}")
    if (sel_alert or "All") != "All":
        active.append(f"Alert = {sel_alert}")
    if iot_filter:
        active.append("IoT only")
    suffix = f" · Filtered by {', '.join(active)}" if active else ""
    st.caption(f"Showing {len(filtered)} of {len(df)} turbines{suffix}")

    if len(filtered) == 0:
        st.info("No turbines match the current filters. Adjust the filters or press Reset.")
        return

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Summary charts ──────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.pie(
            status_counts, values='Count', names='Status',
            title='Turbine Status', color='Status',
            color_discrete_map={'Online': COLORS['ok'], 'Maintenance': COLORS['warn'],
                                'Offline': COLORS['crit']},
            hole=0.45,
        )
        style_fig(fig, 260)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

    with c2:
        company_counts = df['company'].value_counts().reset_index()
        company_counts.columns = ['Company', 'Count']
        fig2 = px.bar(
            company_counts, x='Company', y='Count',
            title='Turbines by Company', color='Count',
            color_continuous_scale='Greens', text='Count',
        )
        style_fig(fig2, 260)
        fig2.update_layout(coloraxis_showscale=False)
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, width='stretch', config={'displayModeBar': False})

    with c3:
        alert_counts = df['alert_level'].value_counts().reset_index()
        alert_counts.columns = ['Alert', 'Count']
        fig3 = px.bar(
            alert_counts, x='Alert', y='Count', title='Alert Levels',
            color='Alert',
            color_discrete_map={'Normal': COLORS['ok'], 'Warning': COLORS['warn'],
                                'Critical': COLORS['crit']},
            text='Count',
        )
        style_fig(fig3, 260)
        fig3.update_layout(showlegend=False)
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, width='stretch', config={'displayModeBar': False})

    # Map
    st.markdown("#### Turbine Locations")
    color_map_status = {'Online': COLORS['ok'], 'Maintenance': COLORS['warn'], 'Offline': COLORS['crit']}
    map_df = filtered.copy()
    fig_map = px.scatter_map(
        map_df,
        lat='latitude', lon='longitude',
        color='status', color_discrete_map=color_map_status,
        hover_name='turbine_id',
        hover_data={
            'company': True, 'location': True, 'health_score': True,
            'alert_level': True, 'latitude': False, 'longitude': False,
            'status': False,
        },
        zoom=4.5, center={'lat': 20.5, 'lon': 76.0},
        height=420, title="Wind Farm Locations Across India",
        map_style="carto-positron",
    )
    fig_map.update_layout(
        margin=dict(t=44, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12, color='#1A2332'),
        title=dict(font=dict(color='#1A2332', size=15), x=0.01, xanchor='left'),
    )
    st.plotly_chart(fig_map, width='stretch', config={'displayModeBar': False})

    # Health distribution
    st.markdown("#### Health Score Distribution")
    render_legend([("Healthy (60-100)", 'ok'), ("At risk (40-59)", 'warn'), ("Critical (<40)", 'crit')])
    fig_hist = px.histogram(
        filtered, x='health_score', nbins=20,
        title='Health Score Distribution (Filtered Turbines)',
        labels={'health_score': 'Health Score', 'count': 'Number of Turbines'},
        color_discrete_sequence=['#1E78B8'],
    )
    style_fig(fig_hist, 260)
    st.plotly_chart(fig_hist, width='stretch', config={'displayModeBar': False})

    # Turbine table
    st.markdown("#### Turbine Details")
    display_df = filtered[[
        'turbine_id', 'company', 'location', 'state',
        'capacity_kw', 'install_year', 'turbine_age',
        'iot_equipped', 'health_score', 'status', 'alert_level', 'last_inspection'
    ]].copy()
    display_df['iot_equipped'] = display_df['iot_equipped'].map({True: 'Yes', False: 'No'})
    display_df.columns = [
        'ID', 'Company', 'Location', 'State',
        'Capacity (kW)', 'Install Year', 'Age (Yrs)',
        'IoT', 'Health %', 'Status', 'Alert', 'Last Inspection'
    ]
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=420,
        column_config={
            'Health %': st.column_config.ProgressColumn(
                'Health %', min_value=0, max_value=100, format="%d%%")
        },
    )
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="Download filtered data as CSV",
        data=csv, file_name="windtrack_assets.csv", mime="text/csv",
    )