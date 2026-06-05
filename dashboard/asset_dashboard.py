import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np
import plotly.graph_objects as go

# Load date
def load_turbines():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'turbines.csv')
    df = pd.read_csv(path)
    return df

def show():

    df = load_turbines()

    # Page Load
    st.title("🏭 Asset Dashboard")
    st.caption("Real-time overview of all wind turbines across the farm network")
    st.markdown("---")

    # KPI row
    total = len(df)
    online      = len(df[df['status'] == 'Online'])
    maintenance = len(df[df['status'] == 'Maintenance'])
    offline     = len(df[df['status'] == 'Offline'])
    iot_count   = len(df[df['iot_equipped'] == True])
    critical    = len(df[df['alert_level'] == 'Critical'])
    avg_health  = round(df['health_score'].mean(), 1)

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Total Turbines",   total)
    k2.metric("🟢 Online",         online)
    k3.metric("🟡 Maintenance",    maintenance)
    k4.metric("🔴 Offline",        offline)
    k5.metric("📡 IoT Equipped",   iot_count)
    k6.metric("⚠️ Critical Alerts", critical)
    k7.metric("Avg Health Score", f"{avg_health}%")

    st.markdown("---")

    # Filter row
    st.subheader("🔍 Filters")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        companies = ["All"] + sorted(df['company'].unique().tolist())
        sel_company = st.selectbox("Company", companies)

    with f2:
        states = ["All"] + sorted(df['state'].unique().tolist())
        sel_state = st.selectbox("State", states)

    with f3:
        sel_status = st.selectbox("Status", ["All", "Online", "Maintenance", "Offline"])

    with f4:
        sel_alert = st.selectbox("Alert Level", ["All", "Normal", "Warning", "Critical"])

    iot_filter = st.checkbox("Show only IoT-equipped turbines", value=False)


    # Apply filters
    filtered = df.copy()
    if sel_company != "All":
        filtered = filtered[filtered['company'] == sel_company]
    if sel_state != "All":
        filtered = filtered[filtered['state'] == sel_state]
    if sel_status != "All":
        filtered = filtered[filtered['status'] == sel_status]
    if sel_alert != "All":
        filtered = filtered[filtered['alert_level'] == sel_alert]
    if iot_filter:
        filtered = filtered[filtered['iot_equipped'] == True]
    st.caption(f"Showing {len(filtered)} of {total} turbines")
    
    st.markdown("---")
    # Charts row
    c1, c2, c3 = st.columns(3)

    with c1:
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.pie(
            status_counts, values='Count', names='Status',
            title='Turbine Status',
            color='Status',
            color_discrete_map={
                'Online': '#2E9E56',
                'Maintenance': '#FFA726',
                'Offline': '#EF5350'
            },
            hole=0.45
        )
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        company_counts = df['company'].value_counts().reset_index()
        company_counts.columns = ['Company', 'Count']
        fig2 = px.bar(
            company_counts, x='Company', y='Count',
            title='Turbines by Company',
            color='Count',
            color_continuous_scale='Greens',
            text='Count'
        )
        fig2.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260,
                           coloraxis_showscale=False)
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        alert_counts = df['alert_level'].value_counts().reset_index()
        alert_counts.columns = ['Alert', 'Count']
        color_map = {'Normal': '#2E9E56', 'Warning': '#FFA726', 'Critical': '#EF5350'}
        fig3 = px.bar(
            alert_counts, x='Alert', y='Count',
            title='Alert Levels',
            color='Alert',
            color_discrete_map=color_map,
            text='Count'
        )
        fig3.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260,
                           showlegend=False)
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    # Map
    st.subheader("🗺️ Turbine Locations")

    color_map_status = {'Online': '#2E9E56', 'Maintenance': '#FFA726', 'Offline': '#EF5350'}
    map_df = filtered.copy()
    map_df['color'] = map_df['status'].map(color_map_status)
    fig_map = px.scatter_mapbox(
        map_df,
        lat='latitude', lon='longitude',
        color='status',
        color_discrete_map=color_map_status,
        hover_name='turbine_id',
        hover_data={
            'company': True,
            'location': True,
            'health_score': True,
            'alert_level': True,
            'latitude': False,
            'longitude': False,
            'status': False
        },
        zoom=4.5,
        center={'lat': 20.5, 'lon': 76.0},
        height=420,
        title="Wind Farm Locations Across India"
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin=dict(t=40, b=0, l=0, r=0)
    )

    st.plotly_chart(fig_map, use_container_width=True)

    # Health score distribution
    st.subheader("📊 Health Score Distribution")
    fig_hist = px.histogram(
        filtered, x='health_score', nbins=20,
        color_discrete_sequence=['#2E9E56'],
        title='Health Score Distribution (Filtered Turbines)',
        labels={'health_score': 'Health Score', 'count': 'Number of Turbines'}
    )
    fig_hist.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=260)
    st.plotly_chart(fig_hist, use_container_width=True)

    # Turbine table
    st.subheader("📋 Turbine Details")

    display_df = filtered[[
        'turbine_id', 'company', 'location', 'state',
        'capacity_kw', 'install_year', 'turbine_age',
        'iot_equipped', 'health_score', 'status', 'alert_level', 'last_inspection'
    ]].copy()

    # Add emoji badges
    display_df['iot_equipped'] = display_df['iot_equipped'].map(
        {True: '✅ Yes', False: '❌ No'}
    )
    display_df['alert_level'] = display_df['alert_level'].map(
        {'Normal': '🟢 Normal', 'Warning': '🟡 Warning', 'Critical': '🔴 Critical'}
    )
    display_df['status'] = display_df['status'].map(
        {'Online': '🟢 Online', 'Maintenance': '🟡 Maintenance', 'Offline': '🔴 Offline'}
    )

    display_df.columns = [
        'ID', 'Company', 'Location', 'State',
        'Capacity (kW)', 'Install Year', 'Age (Yrs)',
        'IoT', 'Health %', 'Status', 'Alert', 'Last Inspection'
    ]
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            'Health %': st.column_config.ProgressColumn(
                'Health %',
                min_value=0,
                max_value=100,
                format="%d%%"
            )
        }
    )
    # Download button
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv,
        file_name="windtrack_assets.csv",
        mime="text/csv"
    )