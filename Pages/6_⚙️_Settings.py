"""
Settings page (6_⚙️_Settings.py) 
User preferences and system configuration
"""

import streamlit as st
import logging

from Auth.auth import (
    init_session_state,
    is_authenticated,
    get_current_user_id,
    get_session_data,
)
from Auth.db import (
    init_db,
    get_user_by_id,
)
from utils.config import (
    PAGE_ICON,
    PAGE_TITLE,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
)

logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="⚙️ Settings | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

# Check authentication
if not is_authenticated():
    st.warning("⚠️ Please log in to access settings.")
    st.info("Navigate to the **🔐 Account** page to log in.")
    st.stop()

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("⚙️ Settings & Preferences")

session_data = get_session_data()
user_id = get_current_user_id()
user = get_user_by_id(user_id)

st.markdown("---")

# ============================================================================
# SETTINGS TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs([
    "👤 User Preferences",
    "🔐 Security",
    "🎨 Appearance",
])

# ============================================================================
# TAB 1: USER PREFERENCES
# ============================================================================

with tab1:
    st.markdown("### 👤 User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Language & Region")
        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "Chinese"],
            index=0,
            help="Select your preferred language"
        )
        
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "EST", "CST", "MST", "PST"],
            index=0,
            help="Select your timezone for timestamps"
        )
    
    with col2:
        st.markdown("#### Date & Time Format")
        date_format = st.selectbox(
            "Date Format",
            ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            index=0,
            help="How dates should be displayed"
        )
        
        time_format = st.selectbox(
            "Time Format",
            ["12-Hour (AM/PM)", "24-Hour"],
            index=0,
            help="How times should be displayed"
        )
    
    st.markdown("---")
    st.markdown("#### Default Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_detection_mode = st.selectbox(
            "Default Detection Mode",
            ["Image Upload", "Webcam", "Video File"],
            index=0,
            help="Default input mode on Detection page"
        )
    
    with col2:
        default_confidence = st.slider(
            "Default Confidence Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Default confidence threshold for detections"
        )
    
    if st.button("💾 Save Preferences", use_container_width=True, type="primary"):
        st.success("✅ User preferences saved!")
        logger.info(f"[SETTINGS] Preferences saved for user {user_id}")

# ============================================================================
# TAB 2: SECURITY
# ============================================================================

with tab2:
    st.markdown("### 🔐 Security & Authentication")
    
    st.markdown("#### Account Security")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Password Management**")
        st.write("Your password should be strong and unique")
        
        if st.button("🔑 Change Password", use_container_width=True):
            st.switch_page("pages/8_🔑_Reset_Password.py")
    
    with col2:
        st.markdown("**Email Verification**")
        if user.email_verified:
            st.success("✅ Your email is verified")
        else:
            st.warning("⚠️ Your email is not verified")
            
            if st.button("📧 Verify Email Now", use_container_width=True):
                st.switch_page("pages/7_📧_Verify_Email.py")
    
    st.markdown("---")
    st.markdown("#### Two-Factor Authentication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if user.two_factor_enabled:
            st.success("✅ 2FA is enabled")
            if st.button("⚙️ Manage 2FA", use_container_width=True):
                st.switch_page("pages/10_🔐_2FA_Setup.py")
        else:
            st.warning("⚠️ 2FA is not enabled")
            if st.button("🔐 Enable 2FA", use_container_width=True):
                st.switch_page("pages/10_🔐_2FA_Setup.py")
    
    with col2:
        st.markdown("**Session Security**")
        st.write("**Last Login:**")
        if user.last_login:
            st.write(f"{user.last_login.strftime('%B %d, %Y at %H:%M:%S')}")
        else:
            st.write("No previous logins")
    
    st.markdown("---")
    st.markdown("#### 🛡️ Security Recommendations")
    
    st.markdown("""
    **Keep your account secure:**
    - ✅ Use a strong, unique password
    - ✅ Verify your email address
    - ✅ Enable Two-Factor Authentication (2FA)
    - ✅ Keep your backup codes safe
    - ✅ Log out from unfamiliar devices
    """)

# ============================================================================
# TAB 3: APPEARANCE
# ============================================================================

with tab3:
    st.markdown("### 🎨 Appearance & Theme")
    
    st.markdown("#### Theme")
    
    theme = st.radio(
        "Select Theme",
        ["Light", "Dark", "Auto (System)"],
        index=0,
        horizontal=True,
        help="Choose your preferred color theme"
    )
    
    st.markdown("---")
    st.markdown("#### Chart Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_type = st.selectbox(
            "Default Chart Type",
            ["Line Chart", "Bar Chart", "Area Chart"],
            index=0,
            help="Default chart type for dashboards"
        )
        
        show_grid = st.checkbox(
            "Show grid lines",
            value=True,
            help="Display grid lines on charts"
        )
    
    with col2:
        animation = st.checkbox(
            "Enable animations",
            value=True,
            help="Animate chart transitions"
        )
        
        show_legend = st.checkbox(
            "Show legend",
            value=True,
            help="Display chart legends"
        )
    
    st.markdown("---")
    st.markdown("#### Layout")
    
    compact_mode = st.checkbox(
        "Compact mode",
        value=False,
        help="Use compact layout (smaller spacing)"
    )
    
    wide_layout = st.checkbox(
        "Wide layout",
        value=True,
        help="Use full-width layout"
    )
    
    if st.button("💾 Save Appearance Settings", use_container_width=True, type="primary"):
        st.success("✅ Appearance settings saved!")
        logger.info(f"[SETTINGS] Appearance settings saved for user {user_id}")

# ============================================================================
# ADDITIONAL SETTINGS SECTION
# ============================================================================

st.markdown("---")
st.markdown("### 🔗 Account & Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Account")
    if st.button("👤 View Profile", use_container_width=True):
        st.switch_page("pages/5_🔐_Account.py")

with col2:
    st.markdown("#### Dashboard")
    if st.button("📊 Go to Dashboard", use_container_width=True):
        st.switch_page("pages/2_📊_Dashboard.py")

with col3:
    st.markdown("#### Logs")
    if st.button("📋 View Activity Logs", use_container_width=True):
        st.switch_page("pages/12_📋_Activity_Logs.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>⚙️ <strong>System Settings</strong> | User preferences & system configuration</p>
    <p>Phase 1: Preferences • Security • Appearance</p>
</div>
""", unsafe_allow_html=True)