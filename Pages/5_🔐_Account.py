"""
Account Management page (5_🔐_Account.py)
Login & Registration for unauthenticated users
Profile management for authenticated users
"""

import streamlit as st
import logging
from datetime import datetime
import time

from Auth.auth import (
    init_session_state,
    is_authenticated,
    register_user,
    login_user,
    logout_user,
    get_session_data,
    get_current_user_id,
    get_user_organizations,
)
from Auth.db import (
    init_db,
    get_user_by_id,
    update_user,
    get_user_activity_logs,
    get_organization_member_count,
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
    page_title="🔐 Account | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 0.75rem;
        padding: 1.5rem;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 0.75rem;
        padding: 1.5rem;
    }
    
    .password-requirements {
        background: #f3f4f6;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

if not is_authenticated():
    # ========================================================================
    # UNAUTHENTICATED: LOGIN & REGISTER TABS
    # ========================================================================
    
    st.title("🔐 Account Management")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    # ====================================================================
    # LOGIN TAB
    # ====================================================================
    with tab1:
        st.markdown("### Sign In to Your Account")
        st.info("🔐 Don't have an account? Switch to the **📝 Register** tab to create one!")
        
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input(
                "📧 Email Address",
                placeholder="user@example.com",
                help="Enter your registered email address"
            )
            
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Enter your password",
                help="Your account password"
            )
            
            remember_me = st.checkbox("Remember me", value=False)
            
            submit = st.form_submit_button(
                "🔓 Login",
                use_container_width=True,
                type="primary"
            )
            
            if submit:
                if not email or not password:
                    st.error("❌ Please enter both email and password")
                    logger.warning("[ACCOUNT] Login attempt with empty fields")
                else:
                    with st.spinner("🔐 Signing in..."):
                        success, message = login_user(email, password)
                        
                        if success:
                            if message == "2FA_REQUIRED":
                                st.warning("🔐 2FA verification required")
                                st.switch_page("pages/11_🔐_2FA_Login.py")
                            else:
                                # ✅ FIX: Removed st.balloons() animation
                                st.success(message)
                                logger.info(f"[ACCOUNT] Login successful for: {email}")
                                # ✅ FIX: Reduced delay for faster redirect
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.error(message)
                            logger.warning(f"[ACCOUNT] Login failed: {message}")
        
        st.markdown("---")
        st.markdown("### 💡 Help & Support")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 🔑 Forgot Password?")
            if st.button("Reset Your Password", use_container_width=True, key="forgot_btn"):
                st.switch_page("pages/9_🔑_Forgot_Password.py")
        
        with col2:
            st.markdown("#### 📧 Email Not Verified?")
            if st.button("Verify Your Email", use_container_width=True, key="verify_btn"):
                st.switch_page("pages/7_📧_Verify_Email.py")
        
        st.markdown("---")
        st.markdown("""
        ### 🚨 Troubleshooting
        
        **Can't log in?**
        - ✅ Verify your email spelling
        - ✅ Check if you've registered first
        - ✅ Passwords are case-sensitive
        
        **Forgot your password?**
        - Click **Reset Your Password** above
        
        **Email verification issue?**
        - Click **Verify Your Email** above
        """)
    
    # ====================================================================
    # REGISTER TAB
    # ====================================================================
    with tab2:
        st.markdown("### Create a New Account")
        st.success("🎉 Join now to start managing PPE compliance!")
        
        with st.form("register_form", clear_on_submit=True):
            name = st.text_input(
                "👤 Full Name",
                placeholder="John Doe",
                help="Your full name"
            )
            
            email = st.text_input(
                "📧 Email Address",
                placeholder="user@example.com",
                help="A unique email address for your account"
            )
            
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Enter a strong password",
                help="Min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char"
            )
            
            confirm_password = st.text_input(
                "🔐 Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                help="Must match the password above"
            )
            
            if password:
                st.markdown("**Password Requirements:**")
                
                requirements = {
                    "✅ At least 8 characters": len(password) >= 8,
                    "✅ Has uppercase letter (A-Z)": any(c.isupper() for c in password),
                    "✅ Has lowercase letter (a-z)": any(c.islower() for c in password),
                    "✅ Has digit (0-9)": any(c.isdigit() for c in password),
                    "✅ Has special character": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
                }
                
                cols = st.columns(2)
                for idx, (check, passed) in enumerate(requirements.items()):
                    with cols[idx % 2]:
                        if passed:
                            st.markdown(f"**{check}**")
                        else:
                            st.markdown(f":grey[{check.replace('✅', '❌')}]")
            
            st.markdown("---")
            
            if password and confirm_password:
                if password == confirm_password:
                    st.success("✅ Passwords match")
                else:
                    st.error("❌ Passwords do not match")
            
            st.markdown("---")
            
            terms_agreed = st.checkbox(
                "✅ I agree to the Terms of Service and Privacy Policy",
                value=False,
                help="You must accept the terms to register"
            )
            
            submit = st.form_submit_button(
                "✅ Create Account",
                use_container_width=True,
                type="primary"
            )
            
            if submit:
                if not all([name, email, password, confirm_password]):
                    st.error("❌ Please fill in all fields")
                elif not terms_agreed:
                    st.error("❌ You must accept the terms and conditions")
                else:
                    with st.spinner("📝 Creating your account..."):
                        try:
                            success, message = register_user(email, password, confirm_password, name)
                            if success:
                                st.success(message)
                                st.info("📧 Check your email for the verification link (expires in 24 hours)")
                                st.success("✅ After verifying your email, you can log in!")
                                logger.info(f"[ACCOUNT] Registration successful for: {email}")
                            else:
                                st.error(f"❌ {message}")
                                logger.warning(f"[ACCOUNT] Registration failed: {message}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            logger.error(f"[ACCOUNT] Registration error: {str(e)}", exc_info=True)
        
        st.markdown("---")
        st.markdown("""
        ### 🔐 What Happens Next?
        
        1. **Create Account** - Click the button above
        2. **Check Email** - You'll receive a verification email
        3. **Verify Email** - Click the link in the email (valid 24 hours)
        4. **Log In** - Use your email and password to sign in
        5. **Start Using** - Create or join an organization!
        """)

else:
    # ========================================================================
    # AUTHENTICATED: PROFILE MANAGEMENT
    # ========================================================================
    
    st.title("🔐 Account Management")
    st.markdown("---")
    
    session_data = get_session_data()
    user_id = get_current_user_id()
    
    st.markdown(f"### 👋 Welcome, {session_data['name']}!")
    st.success(f"✅ Logged in as {session_data['email']}")
    
    # Tabs for authenticated users
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "🏢 Organizations", "🔐 Security", "📋 Activity"])
    
    # ====================================================================
    # PROFILE TAB
    # ====================================================================
    with tab1:
        st.markdown("### Your Profile Information")
        
        user = get_user_by_id(user_id)
        
        if user:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Basic Information")
                st.write(f"**Full Name:** {user.name}")
                st.write(f"**Email:** {user.email}")
                st.write(f"**User ID:** `{user.id}`")
                st.write(f"**Role:** {user.role}")
            
            with col2:
                st.markdown("#### Account Status")
                st.write(f"**Status:** {'🟢 Active' if user.is_active else '🔴 Inactive'}")
                st.write(f"**Email Verified:** {'✅ Yes' if user.email_verified else '❌ No'}")
                st.write(f"**Joined:** {user.created_at.strftime('%B %d, %Y')}")
                if user.last_login:
                    st.write(f"**Last Login:** {user.last_login.strftime('%B %d, %Y %H:%M:%S')}")
            
            st.markdown("---")
            st.markdown("#### Update Profile")
            
            with st.form("update_profile_form"):
                new_name = st.text_input("Full Name", value=user.name)
                
                submit = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                
                if submit:
                    if new_name and new_name != user.name:
                        updated_user = update_user(user_id, name=new_name)
                        if updated_user:
                            st.success("✅ Profile updated successfully!")
                            logger.info(f"[ACCOUNT] Profile updated for user {user_id}")
                            # ✅ FIX: Updated session state with new name
                            st.session_state['user_name'] = new_name
                            st.rerun()
                        else:
                            st.error("❌ Failed to update profile")
                    else:
                        st.info("ℹ️ No changes made")
    
    # ====================================================================
    # ORGANIZATIONS TAB
    # ====================================================================
    with tab2:
        st.markdown("### Your Organizations")
        
        user_orgs = get_user_organizations()
        
        if user_orgs:
            for org in user_orgs:
                with st.expander(f"📦 {org.name}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {org.description or 'No description'}")
                        st.write(f"**ID:** `{org.id}`")
                    
                    with col2:
                        st.write(f"**Created:** {org.created_at.strftime('%B %d, %Y')}")
                        # ✅ FIX: Use dedicated function to avoid DetachedInstanceError
                        member_count = get_organization_member_count(org.id)
                        st.write(f"**Members:** {member_count}")
                    
                    if st.button(f"📊 View Organization Details", use_container_width=True, key=f"org_details_{org.id}"):
                        st.switch_page("pages/4_🏢_Organizations.py")
        else:
            st.info("👉 You haven't joined any organizations yet.")
            st.markdown("""
            ### 🚀 Next Steps
            1. Go to **🏢 Organizations** page
            2. Create a new organization or ask an admin to invite you
            3. Start managing PPE compliance!
            """)
    
    # ====================================================================
    # SECURITY TAB
    # ====================================================================
    with tab3:
        st.markdown("### 🔐 Security & Authentication")
        
        user = get_user_by_id(user_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Password")
            
            if st.button("🔑 Change Password", use_container_width=True, key="change_password"):
                st.switch_page("pages/8_🔑_Reset_Password.py")
            
            st.markdown("---")
            st.markdown("**Email Verification**")
            if user.email_verified:
                st.success("✅ Your email is verified")
            else:
                st.warning("❌ Your email is not verified")
                if st.button("📧 Verify Email Now", use_container_width=True):
                    st.switch_page("pages/7_📧_Verify_Email.py")
        
        with col2:
            st.markdown("#### Two-Factor Authentication")
            
            if user.two_factor_enabled:
                st.success("✅ 2FA is enabled")
                if st.button("⚙️ Manage 2FA", use_container_width=True):
                    st.switch_page("pages/10_🔐_2FA_Setup.py")
            else:
                st.warning("⚠️ 2FA is not enabled")
                if st.button("🔐 Enable 2FA", use_container_width=True):
                    st.switch_page("pages/10_🔐_2FA_Setup.py")
    
    # ====================================================================
    # ACTIVITY TAB - REAL-TIME UPDATES
    # ====================================================================
    with tab4:
        st.markdown("### 📋 Recent Activity")
        
        # ✅ FIX: Add refresh button for manual updates
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("**Your recent account activities:**")
        with col2:
            if st.button("🔄 Refresh", key="activity_refresh"):
                st.rerun()
        
        try:
            activity_logs = get_user_activity_logs(user_id, limit=10)
            
            if not activity_logs:
                st.info("📭 No activity logs found")
            else:
                for log in activity_logs:
                    action_emoji_map = {
                        "login": "🔐",
                        "logout": "🚪",
                        "password_changed": "🔑",
                        "password_reset_requested": "🔑",
                        "2fa_verified": "🛡️",
                        "backup_code_used": "🔑",
                        "email_verified": "📧",
                    }
                    
                    emoji = action_emoji_map.get(log.action, "📝")
                    action_name = log.action.replace("_", " ").title()
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**{emoji} {action_name}**")
                    
                    with col2:
                        st.write(f"*{log.created_at.strftime('%B %d, %Y %H:%M:%S')}*")
                    
                    with col3:
                        if log.ip_address:
                            st.write(f"`{log.ip_address}`")
        
        except Exception as e:
            st.error(f"❌ Error loading activity: {str(e)}")
            logger.error(f"[ACCOUNT] Error: {str(e)}", exc_info=True)
        
        st.markdown("---")
        
        if st.button("📋 View All Activity Logs", use_container_width=True):
            st.switch_page("pages/12_📋_Activity_Logs.py")
    
    # ====================================================================
    # LOGOUT SECTION
    # ====================================================================
    st.markdown("---")
    st.markdown("### 🚪 Session Management")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/6_⚙️_Settings.py")
    
    with col2:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.switch_page("pages/2_📊_Dashboard.py")
    
    with col3:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout_user()
            st.success("✅ You have been logged out successfully!")
            logger.info(f"[ACCOUNT] User {user_id} logged out")
            # ✅ FIX: Reduced delay for faster redirect
            time.sleep(0.5)
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🔐 <strong>Account Management</strong> | Authentication & Profile Management</p>
    <p>Phase 1: Login • Register • Profile • Security</p>
</div>
""", unsafe_allow_html=True)