"""
Activity Logs page (12_📋_Activity_Logs.py)
Displays user activity history for security and compliance.
PHASE 2: Activity logging and monitoring
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
import pandas as pd

from Auth.auth import (
    init_session_state, require_auth, get_current_user_id
)
from Auth.db import init_db, get_user_activity_logs
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
    page_title="📋 Activity Logs | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

try:
    init_db()
    init_session_state()
except Exception as e:
    st.error(f"❌ Initialization error: {str(e)}")
    logger.error(f"Init error: {str(e)}", exc_info=True)
    st.stop()

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

if not require_auth():
    st.stop()

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
    }
    
    .info-text {
        color: #1f2937;
        font-size: 0.95rem;
    }
    
    .activity-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .activity-action {
        font-weight: bold;
        color: #667eea;
        font-size: 1.1rem;
    }
    
    .activity-timestamp {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .activity-description {
        color: #374151;
        margin-top: 0.5rem;
    }
    
    .action-login {
        border-left-color: #28a745 !important;
    }
    
    .action-logout {
        border-left-color: #6c757d !important;
    }
    
    .action-password {
        border-left-color: #dc3545 !important;
    }
    
    .action-2fa {
        border-left-color: #ffc107 !important;
    }
    
    .action-other {
        border-left-color: #17a2b8 !important;
    }
    
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-number {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .stats-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("📋 Activity Logs")
st.markdown("---")

user_id = get_current_user_id()

st.markdown("""
<p class='info-text'>
View your account activity history. This helps you monitor your account security and identify any suspicious activity.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Filters
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    limit = st.slider(
        "📊 Number of logs to display",
        min_value=10,
        max_value=100,
        value=50,
        step=10
    )

with col2:
    action_filter = st.selectbox(
        "🔍 Filter by action",
        ["All", "Login", "Logout", "Password Reset", "2FA", "Email Verification", "Other"]
    )

with col3:
    st.markdown("**Refresh**")
    if st.button("🔄 Refresh Logs", use_container_width=True):
        st.rerun()

st.markdown("---")

# Get activity logs
try:
    activity_logs = get_user_activity_logs(user_id, limit=limit)
    
    if not activity_logs:
        st.info("📭 No activity logs found")
    else:
        # Filter logs
        filtered_logs = activity_logs
        
        if action_filter != "All":
            filter_map = {
                "Login": "login",
                "Logout": "logout",
                "Password Reset": "password_changed",
                "2FA": ["2fa_verified", "backup_code_used"],
                "Email Verification": "email_verified",
            }
            
            filter_actions = filter_map.get(action_filter, "other")
            
            if isinstance(filter_actions, list):
                filtered_logs = [log for log in filtered_logs if log.action in filter_actions]
            else:
                filtered_logs = [log for log in filtered_logs if log.action == filter_actions]
        
        # Display statistics
        st.markdown("### 📊 Activity Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            login_count = sum(1 for log in activity_logs if log.action == "login")
            st.markdown(f"""
            <div class='stats-box'>
                <div class='stats-label'>🔐 Logins</div>
                <div class='stats-number'>{login_count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            logout_count = sum(1 for log in activity_logs if log.action == "logout")
            st.markdown(f"""
            <div class='stats-box'>
                <div class='stats-label'>🚪 Logouts</div>
                <div class='stats-number'>{logout_count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            password_changes = sum(1 for log in activity_logs if "password" in log.action.lower())
            st.markdown(f"""
            <div class='stats-box'>
                <div class='stats-label'>🔑 Password Changes</div>
                <div class='stats-number'>{password_changes}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            security_events = sum(1 for log in activity_logs if any(x in log.action.lower() for x in ["2fa", "email", "reset"]))
            st.markdown(f"""
            <div class='stats-box'>
                <div class='stats-label'>🛡️ Security Events</div>
                <div class='stats-number'>{security_events}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display logs
        st.markdown(f"### 📜 {len(filtered_logs)} Activities Found")
        
        if not filtered_logs:
            st.info(f"📭 No activities found for filter: {action_filter}")
        else:
            for log in filtered_logs:
                # Determine action styling
                action_lower = log.action.lower()
                
                if "login" in action_lower:
                    action_class = "action-login"
                    action_emoji = "🔐"
                elif "logout" in action_lower:
                    action_class = "action-logout"
                    action_emoji = "🚪"
                elif "password" in action_lower:
                    action_class = "action-password"
                    action_emoji = "🔑"
                elif "2fa" in action_lower or "backup_code" in action_lower:
                    action_class = "action-2fa"
                    action_emoji = "🛡️"
                else:
                    action_class = "action-other"
                    action_emoji = "📝"
                
                # Format action name
                action_name = log.action.replace("_", " ").title()
                
                # Format timestamp
                timestamp = log.created_at
                time_ago = datetime.utcnow() - timestamp
                
                if time_ago.total_seconds() < 60:
                    time_str = "just now"
                elif time_ago.total_seconds() < 3600:
                    minutes = int(time_ago.total_seconds() / 60)
                    time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                elif time_ago.total_seconds() < 86400:
                    hours = int(time_ago.total_seconds() / 3600)
                    time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    days = int(time_ago.total_seconds() / 86400)
                    time_str = f"{days} day{'s' if days > 1 else ''} ago"
                
                # Display activity card
                st.markdown(f"""
                <div class='activity-card {action_class}'>
                    <div class='activity-action'>{action_emoji} {action_name}</div>
                    <div class='activity-timestamp'>⏰ {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({time_str})</div>
                """, unsafe_allow_html=True)
                
                if log.description:
                    st.markdown(f"<div class='activity-description'>{log.description}</div>", unsafe_allow_html=True)
                
                if log.ip_address:
                    st.markdown(f"<div class='activity-description'>📍 IP: {log.ip_address}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export options
        st.markdown("### 📥 Export Logs")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Prepare CSV data
            logs_data = []
            for log in filtered_logs:
                logs_data.append({
                    "Date & Time": log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "Action": log.action.replace("_", " ").title(),
                    "Description": log.description or "-",
                    "IP Address": log.ip_address or "-",
                })
            
            df = pd.DataFrame(logs_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # JSON export
            import json
            
            logs_json_data = []
            for log in filtered_logs:
                logs_json_data.append({
                    "timestamp": log.created_at.isoformat(),
                    "action": log.action,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                })
            
            json_str = json.dumps(logs_json_data, indent=2)
            
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

except Exception as e:
    st.error(f"❌ Error loading activity logs: {str(e)}")
    logger.error(f"[ACTIVITY LOGS] Error: {str(e)}", exc_info=True)

st.markdown("---")

# Security tips
st.markdown("### 🛡️ Security Tips")

st.markdown("""
**Monitor your activity regularly:**
- ✅ Check for unusual login locations or times
- ✅ Look for password changes you didn't make
- ✅ Verify 2FA setup and backup code usage
- ✅ Report suspicious activity immediately

**Keep your account secure:**
- 🔐 Use a strong, unique password
- 🛡️ Enable Two-Factor Authentication
- 📧 Keep your email address updated
- 🔑 Never share your backup codes
- ⏰ Log out from unfamiliar devices

**If you see suspicious activity:**
1. Change your password immediately
2. Enable 2FA if not already enabled
3. Review connected devices and sessions
4. Contact support if you suspect unauthorized access
""")

st.markdown("---")

# Navigation
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("⚙️ Back to Settings", use_container_width=True):
        st.switch_page("pages/6_⚙️_Settings.py")

with col2:
    if st.button("🏠 Go to Home", use_container_width=True):
        st.switch_page("pages/1_🏠_Home.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>📋 <strong>Activity Logs</strong> | Monitor your account security</p>
    <p>Phase 2: Activity logging and tracking | Last 100 activities stored</p>
</div>
""", unsafe_allow_html=True)