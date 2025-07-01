import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

DB_PATH = 'data/monitoring.db'

def get_data(query):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def delete_service_records(service_name):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM service_checks WHERE service_name = ?', (service_name,))
    conn.commit()
    conn.close()

def getGraphByAgentType(agent_type):
    records = get_data(f'SELECT * FROM service_checks where agent_type = \'{agent_type}\' ORDER BY timestamp DESC')
    return px.line(
        records,
        x="timestamp",
        y="response_time",
        color="service_name",
        markers=True,
        labels={"response_time": "Response Time (ms)", "timestamp": "Time", "service_name": "Service"},
        title="Response time trends for all services"
    )

st.title('Service Monitoring Dashboard')
st.subheader('Current Service Status')

latest_checks = get_data("""
    SELECT service_name, agent_type, target, MAX(timestamp) as last_check, success
    FROM service_checks
    GROUP BY service_name
    ORDER BY last_check DESC
""")



if latest_checks.empty:
    st.info("No monitoring records found.")
else:
    # Render header row
    header_cols = st.columns([1, 2, 1, 2, 2, 1])
    header_cols[0].markdown("**Action**")
    header_cols[1].markdown("**Service Name**")
    header_cols[2].markdown("**Agent**")
    header_cols[3].markdown("**Target**")
    header_cols[4].markdown("**Last Check**")
    header_cols[5].markdown("**Status**")

    # Render each row with a delete button
    for idx, row in latest_checks.iterrows():
        cols = st.columns([1, 2, 1, 2, 2, 1])

        # Delete button
        if cols[0].button('❌', key=f'del_{row["service_name"]}'):
            delete_service_records(row['service_name'])
            st.success(f'All records for service "{row["service_name"]}" deleted.')
            st.experimental_rerun()  # Use this to refresh the app after deletion

        cols[1].write(row['service_name'])
        cols[2].write(row['agent_type'])
        cols[3].write(row['target'])
        cols[4].write(row['last_check'])
        status_icon = '🟢 UP' if row['success'] == 1 else '🔴 DOWN'
        cols[5].write(status_icon)

    st.markdown("---")

    st.subheader("Response Time Trends for Ping Services")
    ping_chart = getGraphByAgentType("ping")
    st.plotly_chart(ping_chart)

    st.subheader("Response Time Trends for DNS Services")
    dns_chart = getGraphByAgentType("dns")
    st.plotly_chart(dns_chart)

    st.subheader("Response Time Trends for HTTP Services")
    http_chart = getGraphByAgentType("http")
    st.plotly_chart(http_chart)


    all_records = get_data("SELECT * FROM service_checks ORDER BY timestamp DESC")
    
    # Response time trends
    service_names = all_records['service_name'].unique()
    if len(service_names) > 0:
        service = st.selectbox('Select Service for Response Time Trend', service_names)
        service_data = all_records[all_records['service_name'] == service]
        if not service_data.empty:
            st.subheader(f'Response Time Trend: {service}')
            fig = px.line(service_data, x='timestamp', y='response_time', markers=True)
            st.plotly_chart(fig)

    # Uptime statistics
    st.subheader('Uptime Metrics')
    uptime_stats = all_records.groupby('service_name').agg(
        uptime_percent=('success', 'mean'),
        total_checks=('success', 'count')
    )
    uptime_stats['uptime_percent'] *= 100
    if not uptime_stats.empty:
        st.bar_chart(uptime_stats['uptime_percent'])
    else:
        st.info("No uptime data to display.")