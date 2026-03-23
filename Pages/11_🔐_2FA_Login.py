"""
2FA Login page (11_🔐_2FA_Login.py)
Handles Two-Factor Authentication verification during login.
Users can enter TOTP code or backup code.
PHASE 2: 2FA login flow
"""

import streamlit as st
import logging
from datetime import datetime

from Auth.auth import init_session_state, verify_2fa_token, verify_2fa_backup_code
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
    page_title="🔐 2FA Verification | PPE Detection Platform",
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
    
    .tab-content {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("🔐 Two-Factor Authentication")
st.markdown("---")

# Initialize session state with valid key names (no leading numbers)
if "twofa_pending" not in st.session_state:
    st.session_state.twofa_pending = False

if "twofa_user_id" not in st.session_state:
    st.session_state.twofa_user_id = None

if "twofa_attempt" not in st.session_state:
    st.session_state.twofa_attempt = 0

if "twofa_method" not in st.session_state:
    st.session_state.twofa_method = "totp"

if "twofa_result" not in st.session_state:
    st.session_state.twofa_result = None

# Check if 2FA is pending
if not st.session_state.get("twofa_pending"):
    st.markdown("""
    <div class='error-box'>
        <h2 style='color: #721c24; margin: 0;'>❌ No 2FA Verification in Progress</h2>
        <p style='color: #721c24; font-size: 1rem; margin: 0.5rem 0;'>Please log in first to verify with 2FA.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🔐 Back to Login", use_container_width=True):
        st.switch_page("pages/5_🔐_Account.py")

else:
    # 2FA Verification in progress
    if st.session_state.twofa_result is None:
        st.markdown("""
        <div class='info-box'>
            <h2 style='color: #0c5460; margin: 0;'>🔐 Verify Your Identity</h2>
            <p style='color: #0c5460; font-size: 1rem; margin: 0.5rem 0;'>Enter a code from your authenticator app to complete login.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tab selection
        tab1, tab2 = st.tabs(["📱 Authenticator App", "🔑 Backup Code"])
        
        with tab1:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            st.markdown("Enter the 6-digit code from your authenticator app:")
            
            with st.form("totp_form"):
                totp_code = st.text_input(
                    "🔢 6-Digit Code",
                    placeholder="000000",
                    max_chars=6,
                    help="Enter the code from your authenticator app (Google Authenticator, Authy, etc.)",
                    key="totp_input"
                )
                
                submit = st.form_submit_button(
                    "✅ Verify Code",
                    use_container_width=True,
                    type="primary"
                )
                
                if submit:
                    if not totp_code or len(totp_code) != 6:
                        st.error("❌ Please enter a valid 6-digit code")
                        logger.warning(f"[2FA LOGIN] Invalid TOTP format from user {st.session_state.twofa_user_id}")
                    elif not totp_code.isdigit():
                        st.error("❌ Code must contain only numbers")
                        logger.warning(f"[2FA LOGIN] Non-numeric TOTP from user {st.session_state.twofa_user_id}")
                    else:
                        with st.spinner("🔍 Verifying code..."):
                            try:
                                success, message = verify_2fa_token(totp_code)
                                st.session_state.twofa_result = (success, message)
                                
                                if success:
                                    logger.info(f"[2FA LOGIN] TOTP verified for user {st.session_state.twofa_user_id}")
                                else:
                                    st.session_state.twofa_attempt += 1
                                    logger.warning(f"[2FA LOGIN] Invalid TOTP attempt {st.session_state.twofa_attempt}")
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error verifying code: {str(e)}")
                                logger.error(f"[2FA LOGIN] Verification error: {str(e)}", exc_info=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            st.markdown("Enter one of your backup codes:")
            
            with st.form("backup_code_form"):
                backup_code = st.text_input(
                    "🔑 Backup Code",
                    placeholder="XXXX-XXXX-XXXX",
                    help="Enter one of your 10 backup codes (use only if you lost your authenticator app)",
                    key="backup_input"
                )
                
                submit = st.form_submit_button(
                    "✅ Use Backup Code",
                    use_container_width=True,
                    type="primary"
                )
                
                if submit:
                    if not backup_code:
                        st.error("❌ Please enter a backup code")
                        logger.warning(f"[2FA LOGIN] Empty backup code from user {st.session_state.twofa_user_id}")
                    else:
                        with st.spinner("🔍 Verifying backup code..."):
                            try:
                                success, message = verify_2fa_backup_code(backup_code)
                                st.session_state.twofa_result = (success, message)
                                
                                if success:
                                    logger.info(f"[2FA LOGIN] Backup code used for user {st.session_state.twofa_user_id}")
                                else:
                                    st.session_state.twofa_attempt += 1
                                    logger.warning(f"[2FA LOGIN] Invalid backup code attempt {st.session_state.twofa_attempt}")
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error verifying code: {str(e)}")
                                logger.error(f"[2FA LOGIN] Backup code error: {str(e)}", exc_info=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Attempt counter
        if st.session_state.twofa_attempt > 0:
            st.warning(f"⚠️ {st.session_state.twofa_attempt} invalid attempt(s)")
        
        if st.button("🔐 Back to Login", use_container_width=True):
            st.session_state.twofa_pending = False
            st.session_state.twofa_user_id = None
            st.switch_page("pages/5_🔐_Account.py")
    
    else:
        # Display result
        success, message = st.session_state.twofa_result
        
        if success:
            st.markdown("""
            <div class='success-box'>
                <h2 style='color: #155724; margin: 0;'>✅ Login Successful!</h2>
                <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>You have been authenticated.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.success("🎉 Redirecting to dashboard...")
            
            import time
            time.sleep(2)
            st.switch_page("pages/2_📊_Dashboard.py")
        
        else:
            st.markdown(f"""
            <div class='error-box'>
                <h2 style='color: #721c24; margin: 0;'>❌ Verification Failed</h2>
                <p style='color: #721c24; font-size: 1rem; margin: 0.5rem 0;'>{message}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.twofa_result = None
                    st.rerun()
            
            with col2:
                if st.button("🔐 Back to Login", use_container_width=True):
                    st.session_state.twofa_pending = False
                    st.session_state.twofa_user_id = None
                    st.switch_page("pages/5_🔐_Account.py")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🔐 <strong>Two-Factor Authentication</strong> | Secure login verification</p>
    <p>Phase 2: 2FA login | Using TOTP codes or backup codes</p>
</div>
""", unsafe_allow_html=True)