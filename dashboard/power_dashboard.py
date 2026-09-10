# dashboard/power_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sqlite3

from ui import inject_css, style_fig, kpi_card, render_header

COLORS = {'ok': '#16A34A', 'warn': '#D97706', 'crit': '#DC2626'}

# ── Load data ───────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_power():
    """Read power_output + static turbine columns once per hour.

    Returns (merged_df, avg_daily_mwh, top_state_series, top_company_series).
    """
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, '..', 'data', 'windtrack.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM power_output", conn)
    turb = pd.read_sql_query(
        "SELECT turbine_id, company, capacity_kw FROM turbines", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date']  = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['year']  = df['timestamp'].dt.year
    df['hour']  = df['timestamp'].dt.hour

    merged = df.merge(turb, on='turbine_id', how='left')
    avg_daily_mwh = round(merged.groupby('date')['kwh'].sum().mean() / 1000, 1)
    top_state = merged.groupby('state')['kwh'].sum()
    top_company = merged.groupby('company')['kwh'].sum()
    return merged, avg_daily_mwh, top_state, top_company

@st.cache_data(ttl=3600, show_spinner=False)
def load_turbines():
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, '..', 'data', 'windtrack.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM turbines", conn)
    conn.close()
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_historical_kwh():
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, '..', 'data', 'windtrack.db')
    conn = sqlite3.connect(db_path)
    total = pd.read_sql_query(
        "SELECT COALESCE(SUM(kwh), 0) as total FROM power_output", conn
    ).iloc[0]['total']
    conn.close()
    return total

def load_live_kpis():
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base, '..', 'data', 'windtrack.db')
    conn = sqlite3.connect(db_path)
    live_kwh = pd.read_sql_query(
        "SELECT COALESCE(SUM(kwh), 0) as total FROM live_readings", conn
    ).iloc[0]['total']
    latest = pd.read_sql_query("""
        SELECT turbine_id, kwh FROM live_readings
        WHERE timestamp = (SELECT MAX(timestamp) FROM live_readings)
    """, conn)
    conn.close()
    return live_kwh, latest

# ── Aggregation helpers ──
def get_daily(df):
    return df.groupby(['turbine_id', 'date', 'state'])['kwh'].sum().reset_index()

def get_monthly(df):
    return df.groupby(['turbine_id', 'month', 'state'])['kwh'].sum().reset_index()

def get_yearly(df):
    return df.groupby(['turbine_id', 'year', 'state'])['kwh'].sum().reset_index()

@st.fragment(run_every=15)
def show():
    inject_css()
    power_df, avg_daily_mwh, top_state, top_company = load_power()
    turbine_df = load_turbines()

    # ── Page header ─────────────────────────────────────
    render_header(
        "Power Generation",
        "Energy output analysis across all turbines — Daily, Monthly, and Yearly views.",
        live=True,
    )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Farm-level KPIs ──────────────────────────────────
    live_kwh, latest = load_live_kpis()
    total_gwh = round((load_historical_kwh() + live_kwh) / 1_000_000, 2)
    prev_gwh = st.session_state.get('_power_snapshot')
    st.session_state['_power_snapshot'] = total_gwh
    best_turbine = '—'
    best_turbine_kwh = 0.0
    if len(latest) > 0:
        bidx = latest['kwh'].idxmax()
        best_turbine = latest.loc[bidx, 'turbine_id']
        best_turbine_kwh = latest.loc[bidx, 'kwh']

    total_sub = ""
    if prev_gwh is not None:
        diff = round(total_gwh - prev_gwh, 2)
        if diff != 0:
            arrow = '▲' if diff > 0 else '▼'
            tone = COLORS['ok'] if diff > 0 else COLORS['crit']
            total_sub = f'<span style="color:{tone}">{arrow} {abs(diff)} GWh since last tick</span>'

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("Total Output", f"{total_gwh} GWh", total_sub,
                             value_color=COLORS['ok']), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Avg Daily", f"{avg_daily_mwh} MWh/day"),
                    unsafe_allow_html=True)
    with k3:
        best_sub = f"{best_turbine_kwh:,.0f} kWh in latest tick"
        st.markdown(kpi_card("Best Turbine", best_turbine, best_sub),
                    unsafe_allow_html=True)
    with k4:
        state_gwh = f"{top_state.max() / 1_000_000:.2f} GWh"
        st.markdown(kpi_card("Top State", top_state.idxmax(), state_gwh),
                    unsafe_allow_html=True)
    with k5:
        comp_gwh = f"{top_company.max() / 1_000_000:.2f} GWh"
        st.markdown(kpi_card("Top Company", top_company.idxmax(), comp_gwh),
                    unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── View selector tabs ───────────────────────────────
    tab_daily, tab_monthly, tab_yearly, tab_compare = st.tabs([
        "Daily View", "Monthly View", "Yearly Summary", "Turbine Comparison"
    ])

    # ════════════════════════════════════════════════════
    # TAB 1 — DAILY VIEW
    # ════════════════════════════════════════════════════
    with tab_daily:
        st.subheader("Daily Power Output")

        daily_df = get_daily(power_df)

        d1, d2 = st.columns([1, 3])
        with d1:
            # Date range picker
            min_date = pd.Timestamp("2024-01-01").date()
            max_date = pd.Timestamp("2024-12-31").date()
            sel_start = st.date_input("From", value=pd.Timestamp("2024-06-01").date(),
                                       min_value=min_date, max_value=max_date)
            sel_end   = st.date_input("To",   value=pd.Timestamp("2024-06-30").date(),
                                       min_value=min_date, max_value=max_date)
            sel_turbines_d = st.multiselect(
                "Turbines (leave empty = all)",
                options=sorted(power_df['turbine_id'].unique()),
                default=[]
            )

        with d2:
            # Filter
            mask = (daily_df['date'] >= sel_start) & (daily_df['date'] <= sel_end)
            plot_d = daily_df[mask].copy()
            if sel_turbines_d:
                plot_d = plot_d[plot_d['turbine_id'].isin(sel_turbines_d)]

            # Farm total per day
            farm_daily = plot_d.groupby('date')['kwh'].sum().reset_index()
            farm_daily['MWh'] = (farm_daily['kwh'] / 1000).round(1)

            fig_daily = px.bar(
                farm_daily, x='date', y='MWh',
                title=f"Farm Total Daily Output — {sel_start} to {sel_end}",
                labels={'MWh': 'Output (MWh)', 'date': 'Date'},
                color='MWh',
                color_continuous_scale='Greens'
            )
            style_fig(fig_daily, 380)
            fig_daily.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_daily, width='stretch', config={'displayModeBar': False})

        # Per-turbine breakdown for selected range
        st.markdown("##### Per-Turbine Output (Selected Range)")
        turbine_range = plot_d.groupby('turbine_id')['kwh'].sum().reset_index()
        turbine_range['MWh'] = (turbine_range['kwh'] / 1000).round(2)
        turbine_range = turbine_range.sort_values('MWh', ascending=False)

        fig_turb = px.bar(
            turbine_range, x='turbine_id', y='MWh',
            color='MWh', color_continuous_scale='Greens',
            title="Output by Turbine (Selected Date Range)",
            labels={'MWh': 'Output (MWh)', 'turbine_id': 'Turbine'}
        )
        style_fig(fig_turb, 320)
        fig_turb.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_turb, width='stretch', config={'displayModeBar': False})

    # ════════════════════════════════════════════════════
    # TAB 2 — MONTHLY VIEW
    # ════════════════════════════════════════════════════
    with tab_monthly:
        st.subheader("Monthly Power Output")

        monthly_df = get_monthly(power_df)
        farm_monthly = monthly_df.groupby('month')['kwh'].sum().reset_index()
        farm_monthly['GWh'] = (farm_monthly['kwh'] / 1_000_000).round(3)
        farm_monthly = farm_monthly.sort_values('month')

        fig_month = px.line(
            farm_monthly, x='month', y='GWh',
            title="Farm Total Monthly Output — 2024",
            markers=True,
            labels={'GWh': 'Output (GWh)', 'month': 'Month'},
            color_discrete_sequence=['#1E78B8']
        )
        fig_month.update_traces(line=dict(width=3), marker=dict(size=10))
        style_fig(fig_month, 380)
        st.plotly_chart(fig_month, width='stretch', config={'displayModeBar': False})

        # Monthly by state
        state_monthly = monthly_df.groupby(['month', 'state'])['kwh'].sum().reset_index()
        state_monthly['GWh'] = (state_monthly['kwh'] / 1_000_000).round(3)
        state_monthly = state_monthly.sort_values('month')

        fig_state = px.bar(
            state_monthly, x='month', y='GWh',
            color='state',
            title="Monthly Output by State",
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={'GWh': 'Output (GWh)', 'month': 'Month'}
        )
        style_fig(fig_state, 360)
        st.plotly_chart(fig_state, width='stretch', config={'displayModeBar': False})

        # Monthly stats table
        st.markdown("##### Monthly Summary Table")
        summary = farm_monthly[['month', 'GWh']].copy()
        summary.columns = ['Month', 'Output (GWh)']
        summary['vs Avg'] = summary['Output (GWh)'] - summary['Output (GWh)'].mean()
        summary['vs Avg'] = summary['vs Avg'].round(3)
        st.dataframe(summary, width='stretch', hide_index=True)

    # ════════════════════════════════════════════════════
    # TAB 3 — YEARLY SUMMARY
    # ════════════════════════════════════════════════════
    with tab_yearly:
        st.subheader("Yearly Performance Summary — 2024")

        yearly_df = get_yearly(power_df)
        turbine_yearly = yearly_df.groupby('turbine_id')['kwh'].sum().reset_index()
        turbine_yearly = turbine_yearly.merge(
            turbine_df[['turbine_id', 'company', 'state', 'capacity_kw', 'health_score']],
            on='turbine_id'
        )
        turbine_yearly['MWh']          = (turbine_yearly['kwh'] / 1000).round(1)
        turbine_yearly['Capacity Factor %'] = (
            turbine_yearly['kwh'] / (turbine_yearly['capacity_kw'] * 8760) * 100
        ).round(1)
        turbine_yearly = turbine_yearly.sort_values('MWh', ascending=False)

        # Top 10 and bottom 10
        y1, y2 = st.columns(2)

        with y1:
            top10 = turbine_yearly.head(10)
            fig_top = px.bar(
                top10, x='MWh', y='turbine_id',
                orientation='h',
                title="Top 10 Turbines (Annual Output)",
                color='MWh', color_continuous_scale='Greens',
                labels={'MWh': 'Output (MWh)', 'turbine_id': ''}
            )
            style_fig(fig_top, 360)
            fig_top.update_layout(coloraxis_showscale=False,
                                  yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, width='stretch', config={'displayModeBar': False})

        with y2:
            bot10 = turbine_yearly.tail(10)
            fig_bot = px.bar(
                bot10, x='MWh', y='turbine_id',
                orientation='h',
                title="Bottom 10 Turbines (Needs Attention)",
                color='MWh', color_continuous_scale='Reds',
                labels={'MWh': 'Output (MWh)', 'turbine_id': ''}
            )
            style_fig(fig_bot, 360)
            fig_bot.update_layout(coloraxis_showscale=False,
                                  yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bot, width='stretch', config={'displayModeBar': False})

        # Company comparison
        company_yearly = turbine_yearly.groupby('company').agg(
            Total_MWh=('MWh', 'sum'),
            Avg_Health=('health_score', 'mean'),
            Turbine_Count=('turbine_id', 'count')
        ).reset_index().round(1)
        company_yearly['Avg MWh/Turbine'] = (
            company_yearly['Total_MWh'] / company_yearly['Turbine_Count']
        ).round(1)

        fig_comp = px.bar(
            company_yearly, x='company', y='Total_MWh',
            color='company',
            title="Annual Output by Company",
            text='Total_MWh',
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={'Total_MWh': 'Total Output (MWh)', 'company': 'Company'}
        )
        fig_comp.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        style_fig(fig_comp, 360)
        fig_comp.update_layout(showlegend=False)
        st.plotly_chart(fig_comp, width='stretch', config={'displayModeBar': False})

        # Full table
        st.markdown("##### All Turbines — Annual Performance Table")
        display_yearly = turbine_yearly[[
            'turbine_id', 'company', 'state', 'capacity_kw',
            'MWh', 'Capacity Factor %', 'health_score'
        ]].copy()
        display_yearly.columns = [
            'Turbine', 'Company', 'State', 'Capacity (kW)',
            'Annual Output (MWh)', 'Capacity Factor %', 'Health Score'
        ]
        st.dataframe(
            display_yearly, width='stretch', hide_index=True,
            column_config={
                'Capacity Factor %': st.column_config.ProgressColumn(
                    'Capacity Factor %', min_value=0, max_value=100, format="%.1f%%"
                ),
                'Health Score': st.column_config.ProgressColumn(
                    'Health Score', min_value=0, max_value=100, format="%d%%"
                )
            }
        )

    # ════════════════════════════════════════════════════
    # TAB 4 — TURBINE COMPARISON
    # ════════════════════════════════════════════════════
    with tab_compare:
        st.subheader("Compare Turbines Head-to-Head")
        st.caption("Select 2–6 turbines to compare their monthly output side by side.")

        sel_compare = st.multiselect(
            "Select turbines to compare",
            options=sorted(power_df['turbine_id'].unique()),
            default=['WT-001', 'WT-002', 'WT-003']
        )

        if sel_compare:
            monthly_df = get_monthly(power_df)
            compare_df = monthly_df[monthly_df['turbine_id'].isin(sel_compare)].copy()
            compare_df['GWh'] = (compare_df['kwh'] / 1_000_000).round(4)
            compare_df = compare_df.sort_values('month')

            fig_cmp = px.line(
                compare_df, x='month', y='GWh',
                color='turbine_id', markers=True,
                title="Monthly Output Comparison",
                labels={'GWh': 'Output (GWh)', 'month': 'Month', 'turbine_id': 'Turbine'},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_cmp.update_traces(line=dict(width=2.5), marker=dict(size=8))
            style_fig(fig_cmp, 420)
            st.plotly_chart(fig_cmp, width='stretch', config={'displayModeBar': False})

            # Stats table for selected turbines
            yearly_sel = power_df[power_df['turbine_id'].isin(sel_compare)]
            stats = yearly_sel.groupby('turbine_id').agg(
                Total_MWh=('kwh', lambda x: round(x.sum() / 1000, 1)),
                Avg_Hourly_kWh=('kwh', lambda x: round(x.mean(), 1)),
                Peak_kWh=('kwh', 'max'),
                Zero_Hours=('kwh', lambda x: (x == 0).sum())
            ).reset_index()
            stats.columns = ['Turbine', 'Annual (MWh)', 'Avg Hourly (kWh)', 'Peak Hour (kWh)', 'Zero Output Hours']
            st.dataframe(stats, width='stretch', hide_index=True)
        else:
            st.info("Select at least one turbine above to see the comparison.")