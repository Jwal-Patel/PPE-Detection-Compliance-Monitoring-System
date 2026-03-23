"""
Password reset page (8_🔑_Reset_Password.py)
Handles password reset token from email link.
PHASE 2: Password reset flow with comprehensive error handling
"""

import streamlit as st
import logging
from datetime import datetime

from Auth.auth import init_session_state, reset_password
from Auth.db import init_db
from Auth.security import validate_password_strength
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
    page_title="🔑 Reset Password | PPE Detection Platform",
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
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
    }
    
    .info-text {
        color: #1f2937;
        font-size: 0.95rem;
    }
    
    .password-requirements {
        background: #f3f4f6;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
    
    .requirement {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
        font-family: monospace;
    }
    
    .requirement-met {
        color: #28a745;
    }
    
    .requirement-unmet {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("🔑 Reset Your Password")
st.markdown("---")

# Initialize session state keys
if "reset_token" not in st.session_state:
    st.session_state.reset_token = None

if "reset_attempted" not in st.session_state:
    st.session_state.reset_attempted = False

if "reset_result" not in st.session_state:
    st.session_state.reset_result = None

if "password_strength" not in st.session_state:
    st.session_state.password_strength = None

# Extract token from URL query params on first visit
if "token" in st.query_params and st.session_state.reset_token is None:
    st.session_state.reset_token = st.query_params["token"]
    logger.info(f"[PASSWORD RESET] Token received from URL: {st.session_state.reset_token[:20]}...")

# ============================================================================
# PASSWORD STRENGTH CHECKER
# ============================================================================

def check_password_strength(password: str) -> dict:
    """
    Check password strength and return requirements status.
    
    Args:
        password: Password to check
        
    Returns:
        Dictionary with requirement statuses
    """
    requirements = {
        "min_length": len(password) >= 8,
        "has_upper": any(c.isupper() for c in password),
        "has_lower": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
    }
    return requirements

# ============================================================================
# MAIN CONTENT
# ============================================================================

if st.session_state.reset_token:
    token = st.session_state.reset_token
    
    st.markdown("""
    <p class='info-text'>
    Enter your new password below. Your password must be strong and meet all requirements.
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.form("reset_password_form"):
        # Password input
        new_password = st.text_input(
            "🔒 New Password",
            type="password",
            placeholder="Enter your new password",
            help="Your password must meet all requirements below"
        )
        
        # Display password strength requirements
        if new_password:
            requirements = check_password_strength(new_password)
            
            st.markdown("""
            <div class='password-requirements'>
                <strong>Password Requirements:</strong>
            </div>
            """, unsafe_allow_html=True)
            
            req_html = ""
            if requirements["min_length"]:
                req_html += '<div class="requirement requirement-met">✅ At least 8 characters</div>'
            else:
                req_html += '<div class="requirement requirement-unmet">❌ At least 8 characters</div>'
            
            if requirements["has_upper"]:
                req_html += '<div class="requirement requirement-met">✅ 1 uppercase letter (A-Z)</div>'
            else:
                req_html += '<div class="requirement requirement-unmet">❌ 1 uppercase letter (A-Z)</div>'
            
            if requirements["has_lower"]:
                req_html += '<div class="requirement requirement-met">✅ 1 lowercase letter (a-z)</div>'
            else:
                req_html += '<div class="requirement requirement-unmet">❌ 1 lowercase letter (a-z)</div>'
            
            if requirements["has_digit"]:
                req_html += '<div class="requirement requirement-met">✅ 1 digit (0-9)</div>'
            else:
                req_html += '<div class="requirement requirement-unmet">❌ 1 digit (0-9)</div>'
            
            if requirements["has_special"]:
                req_html += '<div class="requirement requirement-met">✅ 1 special character (!@#$%^&*)</div>'
            else:
                req_html += '<div class="requirement requirement-unmet">❌ 1 special character (!@#$%^&*)</div>'
            
            st.markdown(req_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Confirm password input
        confirm_password = st.text_input(
            "🔐 Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            help="Must match your new password"
        )
        
        # Show password match status
        if new_password and confirm_password:
            if new_password == confirm_password:
                st.success("✅ Passwords match")
            else:
                st.error("❌ Passwords do not match")
        
        st.markdown("---")
        
        submit = st.form_submit_button(
            "✅ Reset Password",
            use_container_width=True,
            type="primary",
            disabled=not (new_password and confirm_password)
        )
        
        if submit and not st.session_state.reset_attempted:
            # Validate inputs
            if not new_password or not confirm_password:
                st.error("❌ Please fill in all fields")
                logger.warning("[PASSWORD RESET] Form submission with empty fields")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match")
                logger.warning("[PASSWORD RESET] Passwords do not match")
            else:
                # Attempt password reset
                with st.spinner("🔄 Resetting your password..."):
                    try:
                        success, message = reset_password(token, new_password, confirm_password)
                        
                        st.session_state.reset_attempted = True
                        st.session_state.reset_result = (success, message)
                        
                        if success:
                            logger.info(f"[PASSWORD RESET] Password reset successful")
                        else:
                            logger.warning(f"[PASSWORD RESET] Password reset failed: {message}")
                    except Exception as e:
                        logger.error(f"[PASSWORD RESET] Error during reset: {str(e)}", exc_info=True)
                        st.session_state.reset_attempted = True
                        st.session_state.reset_result = (False, f"An error occurred: {str(e)}")
                
                st.rerun()
    
    # Display reset results
    if st.session_state.reset_result:
        success, message = st.session_state.reset_result
        
        if success:
            # SUCCESS STATE
            st.markdown("""
            <div class='success-box'>
                <h2 style='color: #155724; margin: 0;'>✅ Password Reset Successfully!</h2>
                <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>Your password has been changed. You can now log in with your new password.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            import time
            st.success("🎉 Redirecting to login page in a few seconds...")
            time.sleep(2)
            st.switch_page("pages/5_🔐_Account.py")
        
        else:
            # ERROR STATE
            st.markdown(f"""
            <div class='error-box'>
                <h2 style='color: #721c24; margin: 0;'>❌ Password Reset Failed</h2>
                <p style='color: #721c24; font-size: 1rem; margin: 0.5rem 0;'>{message}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🔧 Troubleshooting")
            
            st.markdown("""
            **Why did this happen?**
            - The reset link has expired (valid for 1 hour)
            - The link was already used to reset your password
            - The link may be corrupted or incorrect
            - Your account may have been deleted
            
            **What you can do:**
            1. Request a new password reset link
            2. Check if you can log in directly (maybe you remember your password)
            3. Contact support if the issue persists
            """)
            
            st.markdown("---")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔐 Back to Login", use_container_width=True):
                    st.switch_page("pages/5_🔐_Account.py")
            with col2:
                if st.button("🆘 Forgot Password Again", use_container_width=True):
                    st.switch_page("pages/9_🔑_Forgot_Password.py")

else:
    # ========================================================================
    # NO TOKEN PROVIDED
    # ========================================================================
    
    st.markdown("""
    <div class='warning-box'>
        <h2 style='color: #856404; margin: 0;'>⚠️ No Reset Link Provided</h2>
        <p style='color: #856404; font-size: 1rem; margin: 0.5rem 0;'>This page requires a valid password reset link from your email.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📧 Request Password Reset")
    
    st.markdown("""
    <p class='info-text'>
    If you forgot your password, please request a password reset link from the login page.
    </p>
    
    **Steps:**
    1. Go to the **Account** (🔐) page
    2. Click on **"Forgot Password?"** link
    3. Enter your email address
    4. Check your email for the reset link
    5. Click the link and follow the instructions
    
    **Didn't receive an email?**
    - Check your spam/junk folder
    - Make sure you use the correct email address
    - Contact support if you continue having issues
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔐 Go to Login", use_container_width=True):
            st.switch_page("pages/5_🔐_Account.py")
    with col2:
        if st.button("🔑 Request Password Reset", use_container_width=True):
            st.switch_page("pages/9_🔑_Forgot_Password.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🔑 <strong>Password Reset</strong> | Change your password securely</p>
    <p>Phase 2: Password reset flow | Tokens expire after 1 hour</p>
</div>
""", unsafe_allow_html=True)    