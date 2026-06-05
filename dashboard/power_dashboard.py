# dashboard/power_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── Load data ───────────────────────────────────────────
@st.cache_data
def load_power():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'power_output.csv')
    df = pd.read_csv(path, parse_dates=['timestamp'])
    # Pre-compute time columns once — cheap to store, saves repeated work
    df['date']  = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['year']  = df['timestamp'].dt.year
    df['hour']  = df['timestamp'].dt.hour
    return df

@st.cache_data
def load_turbines():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'turbines.csv')
    return pd.read_csv(path)

# ── Aggregation helpers (cached separately so filters reuse them) ──
@st.cache_data
def get_daily(df):
    return df.groupby(['turbine_id', 'date', 'state'])['kwh'].sum().reset_index()

@st.cache_data
def get_monthly(df):
    return df.groupby(['turbine_id', 'month', 'state'])['kwh'].sum().reset_index()

@st.cache_data
def get_yearly(df):
    return df.groupby(['turbine_id', 'year', 'state'])['kwh'].sum().reset_index()

def show():
    power_df   = load_power()
    turbine_df = load_turbines()

    # Merge company name into power data
    power_df = power_df.merge(
        turbine_df[['turbine_id', 'company', 'capacity_kw', 'status']],
        on='turbine_id', how='left'
    )

    # ── Page header ─────────────────────────────────────
    st.title("⚡ Power Generation Dashboard")
    st.caption("Energy output analysis across all turbines — Daily, Monthly, and Yearly views.")
    st.markdown("---")

    # ── Farm-level KPIs ──────────────────────────────────
    total_gwh        = round(power_df['kwh'].sum() / 1_000_000, 2)
    avg_daily_mwh    = round(power_df.groupby('date')['kwh'].sum().mean() / 1000, 1)
    best_turbine     = power_df.groupby('turbine_id')['kwh'].sum().idxmax()
    best_turbine_gwh = round(power_df.groupby('turbine_id')['kwh'].sum().max() / 1_000_000, 3)
    top_state        = power_df.groupby('state')['kwh'].sum().idxmax()
    top_company      = power_df.groupby('company')['kwh'].sum().idxmax()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Output",     f"{total_gwh} GWh")
    k2.metric("Avg Daily",        f"{avg_daily_mwh} MWh/day")
    k3.metric("Best Turbine",     best_turbine)
    k4.metric("Top State",        top_state)
    k5.metric("Top Company",      top_company)

    st.markdown("---")

    # ── View selector tabs ───────────────────────────────
    tab_daily, tab_monthly, tab_yearly, tab_compare = st.tabs([
        "📅 Daily View", "📆 Monthly View", "🗓️ Yearly Summary", "🔀 Turbine Comparison"
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
            fig_daily.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=50, b=20, l=0, r=0),
                height=380
            )
            st.plotly_chart(fig_daily, use_container_width=True)

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
        fig_turb.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=50, b=20, l=0, r=0),
            height=320
        )
        st.plotly_chart(fig_turb, use_container_width=True)

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
            color_discrete_sequence=['#2E9E56']
        )
        fig_month.update_traces(line=dict(width=3), marker=dict(size=10))
        fig_month.update_layout(
            margin=dict(t=50, b=20, l=0, r=0),
            height=380
        )
        st.plotly_chart(fig_month, use_container_width=True)

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
        fig_state.update_layout(
            margin=dict(t=50, b=20, l=0, r=0),
            height=360
        )
        st.plotly_chart(fig_state, use_container_width=True)

        # Monthly stats table
        st.markdown("##### Monthly Summary Table")
        summary = farm_monthly[['month', 'GWh']].copy()
        summary.columns = ['Month', 'Output (GWh)']
        summary['vs Avg'] = summary['Output (GWh)'] - summary['Output (GWh)'].mean()
        summary['vs Avg'] = summary['vs Avg'].round(3)
        st.dataframe(summary, use_container_width=True, hide_index=True)

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
                title="🏆 Top 10 Turbines (Annual Output)",
                color='MWh', color_continuous_scale='Greens',
                labels={'MWh': 'Output (MWh)', 'turbine_id': ''}
            )
            fig_top.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=50, b=20, l=0, r=0),
                height=360, yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_top, use_container_width=True)

        with y2:
            bot10 = turbine_yearly.tail(10)
            fig_bot = px.bar(
                bot10, x='MWh', y='turbine_id',
                orientation='h',
                title="⚠️ Bottom 10 Turbines (Needs Attention)",
                color='MWh', color_continuous_scale='Reds',
                labels={'MWh': 'Output (MWh)', 'turbine_id': ''}
            )
            fig_bot.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=50, b=20, l=0, r=0),
                height=360, yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_bot, use_container_width=True)

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
        fig_comp.update_layout(
            showlegend=False,
            margin=dict(t=50, b=20, l=0, r=0),
            height=360
        )
        st.plotly_chart(fig_comp, use_container_width=True)

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
            display_yearly, use_container_width=True, hide_index=True,
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
            fig_cmp.update_layout(
                margin=dict(t=50, b=20, l=0, r=0),
                height=420
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

            # Stats table for selected turbines
            yearly_sel = power_df[power_df['turbine_id'].isin(sel_compare)]
            stats = yearly_sel.groupby('turbine_id').agg(
                Total_MWh=('kwh', lambda x: round(x.sum() / 1000, 1)),
                Avg_Hourly_kWh=('kwh', lambda x: round(x.mean(), 1)),
                Peak_kWh=('kwh', 'max'),
                Zero_Hours=('kwh', lambda x: (x == 0).sum())
            ).reset_index()
            stats.columns = ['Turbine', 'Annual (MWh)', 'Avg Hourly (kWh)', 'Peak Hour (kWh)', 'Zero Output Hours']
            st.dataframe(stats, use_container_width=True, hide_index=True)
        else:
            st.info("Select at least one turbine above to see the comparison.")