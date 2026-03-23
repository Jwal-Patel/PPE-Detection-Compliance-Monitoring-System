"""
Forgot Password page (9_🔑_Forgot_Password.py)
Handles password reset requests - users can request a reset link via email.
PHASE 2: Password reset request flow
"""

import streamlit as st
import logging
from datetime import datetime

from Auth.auth import init_session_state, request_password_reset
from Auth.db import init_db
from Auth.security import validate_email_format
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
    page_title="🔑 Forgot Password | PPE Detection Platform",
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
# STYLING
# ============================================================================

st.markdown("""
<style>
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
    }
    
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
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("🔑 Forgot Your Password?")
st.markdown("---")

# Initialize session state keys
if "forgot_submitted" not in st.session_state:
    st.session_state.forgot_submitted = False

if "forgot_email" not in st.session_state:
    st.session_state.forgot_email = None

if "forgot_result" not in st.session_state:
    st.session_state.forgot_result = None

st.markdown("""
<p class='info-text'>
Don't worry! We'll send you a link to reset your password. Enter your email address below.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Display success message if already submitted
if st.session_state.forgot_submitted and st.session_state.forgot_result:
    st.markdown("""
    <div class='success-box'>
        <h2 style='color: #155724; margin: 0;'>✅ Password Reset Link Sent!</h2>
        <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>Check your email for the password reset link.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📧 What's Next?")
    
    st.markdown(f"""
    <p class='info-text'>
    We've sent a password reset link to <strong>{st.session_state.forgot_email}</strong>.
    </p>
    
    **Instructions:**
    1. Check your email inbox (valid for 1 hour)
    2. Click the **"Reset Password"** button in the email
    3. Enter your new password
    4. Log in with your new password
    
    **Didn't receive an email?**
    - Check your spam/junk folder
    - Make sure you use the correct email address
    - You can request another link below
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.form("resend_reset_form"):
        st.markdown("### 📧 Request Another Reset Link")
        
        email_input = st.text_input(
            "Enter your email address",
            value=st.session_state.forgot_email,
            placeholder="your@email.com",
            help="We'll send a new reset link to this email"
        )
        
        submit = st.form_submit_button(
            "📧 Send Reset Link",
            use_container_width=True,
            type="secondary"
        )
        
        if submit:
            if email_input and "@" in email_input:
                email_valid, email_msg = validate_email_format(email_input.strip())
                if not email_valid:
                    st.error(email_msg)
                    logger.warning(f"[FORGOT PASSWORD] Invalid email format: {email_input}")
                else:
                    try:
                        success, message = request_password_reset(email_input.strip())
                        if success:
                            st.success("✅ Password reset link sent! Check your email.")
                            logger.info(f"[FORGOT PASSWORD] Reset link sent to: {email_input}")
                        else:
                            st.error(message)
                            logger.warning(f"[FORGOT PASSWORD] Reset request failed: {message}")
                    except Exception as e:
                        st.error(f"❌ Error sending reset link: {str(e)}")
                        logger.error(f"[FORGOT PASSWORD] Error: {str(e)}", exc_info=True)
            else:
                st.warning("Please enter a valid email address")

else:
    # Request password reset form
    with st.form("forgot_password_form"):
        email_input = st.text_input(
            "📧 Email Address",
            placeholder="your@email.com",
            help="Enter the email address associated with your account"
        )
        
        st.markdown("---")
        
        submit = st.form_submit_button(
            "📧 Send Password Reset Link",
            use_container_width=True,
            type="primary"
        )
        
        if submit:
            if not email_input:
                st.error("❌ Please enter your email address")
                logger.warning("[FORGOT PASSWORD] Form submission with empty email")
            else:
                # Validate email format
                email_valid, email_msg = validate_email_format(email_input.strip())
                if not email_valid:
                    st.error(email_msg)
                    logger.warning(f"[FORGOT PASSWORD] Invalid email format: {email_input}")
                else:
                    # Request password reset
                    with st.spinner("📧 Sending password reset link..."):
                        try:
                            success, message = request_password_reset(email_input.strip())
                            
                            st.session_state.forgot_submitted = True
                            st.session_state.forgot_email = email_input.strip()
                            st.session_state.forgot_result = (success, message)
                            
                            logger.info(f"[FORGOT PASSWORD] Reset request for: {email_input}")
                        except Exception as e:
                            logger.error(f"[FORGOT PASSWORD] Error: {str(e)}", exc_info=True)
                            st.error(f"❌ Error sending reset link: {str(e)}")
                    
                    st.rerun()

st.markdown("---")

# Navigation
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🔐 Back to Login", use_container_width=True):
        st.switch_page("pages/5_🔐_Account.py")

with col2:
    if st.button("📝 Register Account", use_container_width=True):
        st.switch_page("pages/5_🔐_Account.py")

with col3:
    if st.button("🏠 Go Home", use_container_width=True):
        st.switch_page("pages/1_🏠_Home.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🔑 <strong>Forgot Password</strong> | Request a password reset link</p>
    <p>Phase 2: Password reset request | Reset links expire after 1 hour</p>
</div>
""", unsafe_allow_html=True)