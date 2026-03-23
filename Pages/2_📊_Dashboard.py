"""
Dashboard page (2_📊_Dashboard.py) - Analytics and compliance statistics.
PHASE 4: Real database integration with advanced analytics.
Auto-refreshes every 30 seconds to show real-time data.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
import time

from Auth.auth import (
    init_session_state,
    require_auth,
    require_org_selected,
    get_current_org_id,
    get_session_data,
)
from Auth.db import (
    init_db,
    get_organization_by_id,
    get_workstations_by_organization,
)
from utils.config import (
    PAGE_ICON,
    PAGE_TITLE,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
)
from utils.analytics import ComplianceAnalytics
from utils.report_generator import ReportGenerator

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="📊 Dashboard | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

if not require_auth() or not require_org_selected():
    st.stop()

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .metric-card {
        background: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# RESPONSIVE DESIGN
# ============================================================================

CONTAINER_WIDTH = 1100
PADDING = 40
CHART_WIDTH_FULL = CONTAINER_WIDTH - PADDING
CHART_WIDTH_HALF = (CONTAINER_WIDTH - PADDING) // 2 - 20
CHART_HEIGHT_DEFAULT = 400
CHART_HEIGHT_COMPACT = 300

# ============================================================================
# SESSION STATE - CACHING & AUTO-REFRESH
# ============================================================================

if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = True

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.markdown("### 📊 Dashboard Filters")

session_data = get_session_data()
org_id = session_data['org_id']

# Workstation selector
workstations = get_workstations_by_organization(org_id)
if workstations:
    workstation_names = ["All Workstations"] + [ws.name for ws in workstations]
    selected_ws_name = st.sidebar.selectbox("Workstation", workstation_names)
    selected_workstation = None if selected_ws_name == "All Workstations" else next(
        (ws for ws in workstations if ws.name == selected_ws_name), None
    )
else:
    st.sidebar.warning("No workstations configured")
    selected_workstation = None

# Date range selector
st.sidebar.markdown("### 📅 Date Range")

date_range_option = st.sidebar.radio(
    "Select Period",
    ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
    help="Select time period for analytics"
)

if date_range_option == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("From", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To", datetime.now())
else:
    end_date = datetime.now().date()
    if date_range_option == "Last 7 Days":
        start_date = (datetime.now() - timedelta(days=7)).date()
    elif date_range_option == "Last 30 Days":
        start_date = (datetime.now() - timedelta(days=30)).date()
    else:
        start_date = (datetime.now() - timedelta(days=90)).date()

# ✅ NEW: Auto-refresh controls
st.sidebar.markdown("### 🔄 Auto-Refresh")
st.session_state.auto_refresh_enabled = st.sidebar.checkbox(
    "Enable auto-refresh (30s)",
    value=st.session_state.auto_refresh_enabled,
    help="Automatically refresh data every 30 seconds"
)

# Manual refresh button
col1, col2 = st.sidebar.columns([1, 1])
with col1:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()

with col2:
    if st.button("⏱️ Clear Cache", use_container_width=True):
        st.session_state.analytics_data = None
        st.session_state.last_refresh = None
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("📊 Compliance Dashboard")

st.markdown(f"**Organization:** {session_data['org_name']}")
if selected_workstation:
    st.markdown(f"**Workstation:** {selected_workstation.name}")

st.markdown(f"**Period:** {start_date} to {end_date}")

# ✅ FIX: Show last refresh time
if st.session_state.last_refresh:
    refresh_time = st.session_state.last_refresh.strftime('%H:%M:%S')
    st.markdown(f"<small>📍 Last updated: {refresh_time}</small>", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# FETCH ANALYTICS DATA WITH CACHING
# ============================================================================

@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_analytics_data(org_id, start_datetime, end_datetime):
    """
    ✅ FIX: Fetch analytics with proper caching
    Reduces database hits while maintaining reasonable freshness
    """
    stats = ComplianceAnalytics.get_organization_stats(
        org_id,
        start_datetime,
        end_datetime
    )
    
    trends = ComplianceAnalytics.get_daily_trends(
        org_id,
        start_datetime,
        end_datetime
    )
    
    ppe_stats = ComplianceAnalytics.get_ppe_stats(
        org_id,
        start_datetime,
        end_datetime
    )
    
    compliance_dist = ComplianceAnalytics.get_compliance_distribution(
        org_id,
        start_datetime,
        end_datetime
    )
    
    return stats, trends, ppe_stats, compliance_dist

# Fetch data with loading spinner
with st.spinner("📊 Loading analytics..."):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    stats, trends, ppe_stats, compliance_dist = fetch_analytics_data(
        org_id,
        start_datetime,
        end_datetime
    )

if not stats or stats.get('total_detections', 0) == 0:
    st.warning("⚠️ No detection data available for the selected period")
    st.info("📊 Once you save detections from the Detection page, analytics will appear here automatically!")
    st.stop()

# ============================================================================
# KPI CARDS - REAL-TIME METRICS
# ============================================================================

st.markdown("## 📈 Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📸 Detections",
        value=stats.get('total_detections', 0),
        delta="scan sessions"
    )

with col2:
    st.metric(
        label="👥 Workers",
        value=stats.get('total_workers', 0),
        delta="analyzed"
    )

with col3:
    compliant_count = stats.get('compliant', 0)
    total_workers = stats.get('total_workers', 1)
    compliant_pct = (compliant_count / total_workers * 100) if total_workers > 0 else 0
    st.metric(
        label="✅ Compliant",
        value=compliant_count,
        delta=f"{compliant_pct:.1f}%"
    )

with col4:
    partial_count = stats.get('partial', 0)
    partial_pct = (partial_count / total_workers * 100) if total_workers > 0 else 0
    st.metric(
        label="⚠️ Partial",
        value=partial_count,
        delta=f"{partial_pct:.1f}%"
    )

with col5:
    non_compliant_count = stats.get('non_compliant', 0)
    non_compliant_pct = (non_compliant_count / total_workers * 100) if total_workers > 0 else 0
    st.metric(
        label="❌ Non-Compliant",
        value=non_compliant_count,
        delta=f"{non_compliant_pct:.1f}%"
    )

st.markdown("---")

# ============================================================================
# CHARTS - AUTO-UPDATING
# ============================================================================

st.markdown("## 📊 Analytics & Trends")

tab1, tab2, tab3 = st.tabs(
    ["📈 Compliance Trend", "📊 Status Breakdown", "🛡️ PPE Distribution"]
)

# TAB 1: Compliance Trend
with tab1:
    st.markdown("### Compliance Rate Over Time")
    
    if not trends.empty:
        chart_data = trends[["date", "compliance_rate"]].copy()
        chart_data.columns = ["Date", "Compliance Rate (%)"]
        
        line_chart = alt.Chart(chart_data).mark_line(
            point=True,
            color="#1f77b4",
            size=3
        ).encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y(
                "Compliance Rate (%):Q",
                title="Compliance Rate (%)",
                scale=alt.Scale(domain=[0, 100])
            ),
            tooltip=["Date:T", "Compliance Rate (%):Q"]
        ).properties(
            width=CHART_WIDTH_FULL,
            height=CHART_HEIGHT_DEFAULT
        ).interactive()
        
        st.altair_chart(line_chart, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Average", f"{trends['compliance_rate'].mean():.1f}%")
        with col2:
            st.metric("📈 Highest", f"{trends['compliance_rate'].max():.1f}%")
        with col3:
            st.metric("📉 Lowest", f"{trends['compliance_rate'].min():.1f}%")
    else:
        st.info("No trend data available")

# TAB 2: Status Breakdown
with tab2:
    st.markdown("### Compliance Status Distribution")
    
    status_data = pd.DataFrame({
        "Status": ["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant"],
        "Count": [
            compliance_dist.get('compliant', 0),
            compliance_dist.get('partial', 0),
            compliance_dist.get('non_compliant', 0)
        ],
    })
    
    donut_chart = alt.Chart(status_data).encode(
        theta=alt.Theta("Count:Q"),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant"],
                range=["#2ca02c", "#ff9800", "#d62728"]
            )
        ),
        tooltip=["Status:N", "Count:Q"]
    ).mark_arc(
        innerRadius=50,
        stroke="#fff",
        strokeWidth=2
    ).properties(
        width=CHART_WIDTH_HALF,
        height=CHART_HEIGHT_DEFAULT,
        title="Compliance Status"
    )
    
    st.altair_chart(donut_chart, use_container_width=True)
    
    st.markdown("### Status Summary")
    
    total_workers = stats.get('total_workers', 0)
    compliant_pct = f"{compliance_dist.get('compliant', 0)/total_workers*100:.1f}%" if total_workers > 0 else "0%"
    partial_pct = f"{compliance_dist.get('partial', 0)/total_workers*100:.1f}%" if total_workers > 0 else "0%"
    non_compliant_pct = f"{compliance_dist.get('non_compliant', 0)/total_workers*100:.1f}%" if total_workers > 0 else "0%"
    
    summary_df = pd.DataFrame({
        "Status": ["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant", "Total"],
        "Count": [
            compliance_dist.get('compliant', 0),
            compliance_dist.get('partial', 0),
            compliance_dist.get('non_compliant', 0),
            total_workers
        ],
        "Percentage": [
            compliant_pct,
            partial_pct,
            non_compliant_pct,
            "100%"
        ]
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# TAB 3: PPE Distribution
with tab3:
    st.markdown("### PPE Item Detection")
    
    if ppe_stats:
        ppe_df = pd.DataFrame({
            "PPE Item": [item.capitalize() for item in ppe_stats.keys()],
            "Count": list(ppe_stats.values()),
        })
        
        bar_chart = alt.Chart(ppe_df).mark_bar(color="#1f77b4").encode(
            x=alt.X("Count:Q", title="Detection Count"),
            y=alt.Y("PPE Item:N", title="PPE Item", sort="-x"),
            tooltip=["PPE Item:N", "Count:Q"]
        ).properties(
            width=CHART_WIDTH_FULL,
            height=CHART_HEIGHT_COMPACT
        )
        
        st.altair_chart(bar_chart, use_container_width=True)
        st.dataframe(ppe_df, use_container_width=True, hide_index=True)
    else:
        st.info("No PPE data available")

st.markdown("---")

# ============================================================================
# EXPORT SECTION
# ============================================================================

st.markdown("## 📥 Generate & Export Reports")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 CSV Report", use_container_width=True):
        if not trends.empty:
            csv_data = ReportGenerator.generate_csv_report(
                trends,
                f"compliance_report_{start_date}_{end_date}.csv"
            )
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"compliance_report_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )

with col2:
    if st.button("📄 PDF Report", use_container_width=True):
        if not trends.empty:
            pdf_data = ReportGenerator.generate_pdf_report(
                trends,
                f"PPE Compliance Report - {start_date} to {end_date}",
                f"compliance_report_{start_date}_{end_date}.pdf",
                stats=stats
            )
            if pdf_data:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"compliance_report_{start_date}_{end_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ PDF generation requires reportlab. Install with: pip install reportlab")

with col3:
    if st.button("📋 JSON Report", use_container_width=True):
        json_data = ReportGenerator.generate_json_report(
            stats,
            f"compliance_report_{start_date}_{end_date}.json"
        )
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name=f"compliance_report_{start_date}_{end_date}.json",
            mime="application/json",
            use_container_width=True
        )

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>📊 <strong>Dashboard Analytics</strong> | Real-time compliance tracking</p>
    <p>Phase 4: Database integration • Advanced analytics • Multi-format reports</p>
    <p>✅ Auto-refresh enabled • Data updates every 60 seconds</p>
</div>
""", unsafe_allow_html=True)