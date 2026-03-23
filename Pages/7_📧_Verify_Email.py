"""
Email verification page (7_📧_Verify_Email.py)
Handles email verification token from email link.
PHASE 2: Email verification flow
"""

import streamlit as st
import logging
from datetime import datetime

from Auth.auth import init_session_state, verify_email
from Auth.db import init_db
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
    page_title="📧 Verify Email | PPE Detection Platform",
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
    
    .error-box {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 2px solid #dc3545;
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

st.title("📧 Email Verification")

st.markdown("---")

# Initialize session state keys
if "verification_token" not in st.session_state:
    st.session_state.verification_token = None

if "verification_attempted" not in st.session_state:
    st.session_state.verification_attempted = False

if "verification_result" not in st.session_state:
    st.session_state.verification_result = None

# Extract token from URL query params on first visit
if "token" in st.query_params and st.session_state.verification_token is None:
    st.session_state.verification_token = st.query_params["token"]
    logger.info(f"[EMAIL VERIFICATION] Token received from URL: {st.session_state.verification_token[:20]}...")

# Process verification once per token
if st.session_state.verification_token and not st.session_state.verification_attempted:
    token = st.session_state.verification_token
    
    with st.spinner("🔍 Verifying your email address..."):
        try:
            # Attempt to verify the token
            success, message = verify_email(token)
            
            # Mark as attempted to prevent re-verification on rerun
            st.session_state.verification_attempted = True
            st.session_state.verification_result = (success, message)
            
            logger.info(f"[EMAIL VERIFICATION] Verification result: success={success}, message={message}")
        except Exception as e:
            logger.error(f"[EMAIL VERIFICATION] Error during verification: {str(e)}", exc_info=True)
            st.session_state.verification_attempted = True
            st.session_state.verification_result = (False, f"An error occurred: {str(e)}")
    
    # Force rerun to display the result
    st.rerun()

# Display results
if st.session_state.verification_result:
    success, message = st.session_state.verification_result
    
    if success:
        # ====================================================================
        # SUCCESS STATE
        # ====================================================================
        
        st.markdown("""
        <div class='success-box'>
            <h2 style='color: #155724; margin: 0;'>✅ Email Verified Successfully!</h2>
            <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>Your account is now active and ready to use.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.success("🎉 Redirecting to login page in a few seconds...")
        
        # Auto-redirect to Account page after 2 seconds
        import time
        time.sleep(2)
        st.switch_page("pages/5_🔐_Account.py")
        
        logger.info(f"[EMAIL VERIFICATION] Email verification successful")
    
    else:
        # ====================================================================
        # ERROR STATE
        # ====================================================================
        
        st.markdown(f"""
        <div class='error-box'>
            <h2 style='color: #721c24; margin: 0;'>❌ Verification Failed</h2>
            <p style='color: #721c24; font-size: 1rem; margin: 0.5rem 0;'>{message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔧 Troubleshooting")
        
        st.markdown("""
        **Why did this happen?**
        - The verification link has expired (valid for 24 hours)
        - The link was already used to verify another account
        - The link may be corrupted or incorrect
        - Your account may have been deleted
        
        **What you can do:**
        1. Register again with your email address
        2. Check if you already have an account and can log in directly
        3. Request a new verification email (if registered)
        4. Contact support if the issue persists
        """)
        
        st.markdown("---")
        st.markdown("### 📧 Resend Verification Email")
        
        with st.form("resend_verification_form"):
            email_input = st.text_input(
                "Enter your email address",
                placeholder="your@email.com",
                help="We'll send a new verification link to this email"
            )
            
            submit = st.form_submit_button(
                "📧 Resend Verification Email",
                use_container_width=True,
                type="secondary"
            )
            
            if submit:
                if email_input and "@" in email_input:
                    try:
                        from Auth.auth import resend_verification_email
                        success_resend, msg_resend = resend_verification_email(email_input)
                        if success_resend:
                            st.success(msg_resend)
                            logger.info(f"[EMAIL VERIFICATION] Resend request for: {email_input}")
                        else:
                            st.error(msg_resend)
                            logger.warning(f"[EMAIL VERIFICATION] Resend failed for: {email_input}")
                    except Exception as e:
                        st.error(f"❌ Error sending email: {str(e)}")
                        logger.error(f"[EMAIL VERIFICATION] Resend error: {str(e)}", exc_info=True)
                else:
                    st.warning("Please enter a valid email address")
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔐 Back to Login", use_container_width=True):
                st.switch_page("pages/5_🔐_Account.py")
        with col2:
            if st.button("📝 Register Account", use_container_width=True):
                st.switch_page("pages/5_🔐_Account.py")
        
        logger.error(f"[EMAIL VERIFICATION] Email verification failed: {message}")

else:
    # ========================================================================
    # NO TOKEN PROVIDED
    # ========================================================================
    
    st.warning("⚠️ No verification token provided in the URL")
    
    st.markdown("---")
    st.markdown("### 📧 Email Verification Required")
    
    st.markdown("""
    <p class='info-text'>
    If you've registered for an account, you should have received an email with a verification link.
    </p>
    
    **Steps:**
    1. Check your email inbox (and spam/junk folder)
    2. Click the **"Verify Email Address"** button in the email
    3. You'll be redirected here to verify your account
    
    **Didn't receive an email?**
    - Make sure you used the correct email address when registering
    - Check your spam/junk folder (it might be filtered there)
    - Try registering again with your email
    - Contact support if you continue having issues
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔐 Back to Login", use_container_width=True):
            st.switch_page("pages/5_🔐_Account.py")
    with col2:
        if st.button("📝 Register Account", use_container_width=True):
            st.switch_page("pages/5_🔐_Account.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>📧 <strong>Email Verification</strong> | Verify your email to activate your account</p>
    <p>Phase 2: Email verification flow | Tokens expire after 24 hours</p>
</div>
""", unsafe_allow_html=True)