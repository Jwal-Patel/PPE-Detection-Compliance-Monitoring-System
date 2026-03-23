"""
2FA Setup page (10_🔐_2FA_Setup.py)
Enables Two-Factor Authentication using TOTP (Time-based One-Time Password).
Users scan QR code in authenticator app, then verify with generated code.
PHASE 2: 2FA setup flow
"""

import streamlit as st
import logging
from datetime import datetime

from Auth.auth import init_session_state, get_current_user_id, is_authenticated
from Auth.db import init_db, get_user_by_id, update_user
from Auth.totp import TOTPManager
from Auth.email_service import email_service
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
    page_title="🔐 2FA Setup | PPE Detection Platform",
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

if not is_authenticated():
    st.warning("⚠️ Please log in to access this page.")
    st.info("Navigate to the **🔐 Account** page to log in.")
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
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: left;
    }
    
    .info-text {
        color: #1f2937;
        font-size: 0.95rem;
    }
    
    .backup-codes-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    .backup-code {
        background: white;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("🔐 Set Up Two-Factor Authentication")
st.markdown("---")

user_id = get_current_user_id()
user = get_user_by_id(user_id)

# Initialize session state with valid key names (no leading numbers)
if "twofa_setup_step" not in st.session_state:
    st.session_state.twofa_setup_step = "intro"

if "twofa_secret" not in st.session_state:
    st.session_state.twofa_secret = None

if "twofa_backup_codes" not in st.session_state:
    st.session_state.twofa_backup_codes = None

# Check if 2FA already enabled
if user.two_factor_enabled:
    st.markdown("""
    <div class='info-box'>
        <h2 style='color: #0c5460; margin: 0;'>✅ 2FA Already Enabled</h2>
        <p style='color: #0c5460; font-size: 1rem; margin: 0.5rem 0;'>Your account already has Two-Factor Authentication enabled.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔧 Manage 2FA")
    
    st.markdown("""
    **Your options:**
    - **Regenerate Backup Codes** - Get new backup codes
    - **Disable 2FA** - Turn off Two-Factor Authentication (less secure)
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Regenerate Backup Codes", use_container_width=True):
            try:
                new_backup_codes = TOTPManager.generate_backup_codes()
                update_user(user_id, backup_codes=new_backup_codes)
                st.success("✅ New backup codes generated!")
                st.warning("⚠️ Save these codes in a safe place. You can use them to log in if you lose access to your authenticator app.")
                
                # Display backup codes
                st.markdown("### 📋 Your New Backup Codes")
                st.markdown('<div class="backup-codes-box">', unsafe_allow_html=True)
                for code in new_backup_codes:
                    st.markdown(f'<div class="backup-code">{code}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download option
                codes_text = "\n".join(new_backup_codes)
                st.download_button(
                    label="📥 Download Backup Codes",
                    data=codes_text,
                    file_name="2fa_backup_codes.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                logger.info(f"[2FA SETUP] Backup codes regenerated for user {user_id}")
            except Exception as e:
                st.error(f"❌ Error regenerating codes: {str(e)}")
                logger.error(f"[2FA SETUP] Error: {str(e)}", exc_info=True)
    
    with col2:
        if st.button("❌ Disable 2FA", use_container_width=True):
            try:
                update_user(user_id, two_factor_enabled=False, two_factor_secret=None, backup_codes=None)
                st.warning("⚠️ Two-Factor Authentication has been disabled. Your account is less secure.")
                logger.warning(f"[2FA SETUP] 2FA disabled for user {user_id}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error disabling 2FA: {str(e)}")
                logger.error(f"[2FA SETUP] Error: {str(e)}", exc_info=True)
    
    st.markdown("---")
    
    if st.button("⬅️ Back to Settings", use_container_width=True):
        st.switch_page("pages/6_⚙️_Settings.py")

else:
    # 2FA Setup Flow
    if st.session_state.twofa_setup_step == "intro":
        st.markdown("""
        <div class='info-box'>
            <h2 style='color: #0c5460; margin: 0;'>🔐 Secure Your Account</h2>
            <p style='color: #0c5460; font-size: 1rem; margin: 0.5rem 0;'>Two-Factor Authentication adds an extra layer of security to your account.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### What is Two-Factor Authentication?")
        
        st.markdown("""
        Two-Factor Authentication (2FA) requires you to verify your identity in two ways:
        
        1. **Your Password** - Something you know
        2. **Your Authenticator App** - Something you have
        
        This makes your account much more secure, even if someone learns your password.
        
        **How it works:**
        - You'll scan a QR code with an authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)
        - When you log in, you'll enter a 6-digit code from the app
        - You'll also receive backup codes in case you lose access to your authenticator app
        """)
        
        st.markdown("---")
        st.markdown("### 📱 Before You Start")
        
        st.markdown("""
        **You'll need:**
        - An authenticator app installed on your phone:
            - Google Authenticator
            - Microsoft Authenticator
            - Authy
            - FreeOTP
            - Any other TOTP-compatible app
        
        **Time required:** About 5 minutes
        """)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Start 2FA Setup", use_container_width=True, type="primary"):
                # Generate 2FA secret and backup codes
                try:
                    secret = TOTPManager.generate_secret()
                    backup_codes = TOTPManager.generate_backup_codes()
                    
                    st.session_state.twofa_secret = secret
                    st.session_state.twofa_backup_codes = backup_codes
                    st.session_state.twofa_setup_step = "scan"
                    
                    logger.info(f"[2FA SETUP] Setup started for user {user_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error generating 2FA secret: {str(e)}")
                    logger.error(f"[2FA SETUP] Error: {str(e)}", exc_info=True)
        
        with col2:
            if st.button("⬅️ Back to Settings", use_container_width=True):
                st.switch_page("pages/6_⚙️_Settings.py")
    
    elif st.session_state.twofa_setup_step == "scan":
        st.markdown("""
        <div class='info-box'>
            <h2 style='color: #0c5460; margin: 0;'>Step 1: Scan QR Code</h2>
            <p style='color: #0c5460; font-size: 1rem; margin: 0.5rem 0;'>Use your authenticator app to scan this QR code.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.session_state.twofa_secret:
            try:
                # Generate QR code
                qr_code = TOTPManager.generate_qr_code(
                    secret=st.session_state.twofa_secret,
                    name=user.name,
                    issuer="PPE Detection Platform"
                )
                
                st.image(qr_code, width=300)
                
                st.markdown("---")
                st.markdown("### Or enter manually")
                
                st.markdown(f"""
                If you can't scan the QR code, enter this code in your authenticator app:
                
                **Secret Key:** `{st.session_state.twofa_secret}`
                """)
                
                st.markdown("---")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ I've Scanned the QR Code", use_container_width=True, type="primary"):
                        st.session_state.twofa_setup_step = "verify"
                        st.rerun()
                
                with col2:
                    if st.button("⬅️ Cancel Setup", use_container_width=True):
                        st.session_state.twofa_setup_step = "intro"
                        st.session_state.twofa_secret = None
                        st.session_state.twofa_backup_codes = None
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error generating QR code: {str(e)}")
                logger.error(f"[2FA SETUP] QR code error: {str(e)}", exc_info=True)
    
    elif st.session_state.twofa_setup_step == "verify":
        st.markdown("""
        <div class='info-box'>
            <h2 style='color: #0c5460; margin: 0;'>Step 2: Verify TOTP Code</h2>
            <p style='color: #0c5460; font-size: 1rem; margin: 0.5rem 0;'>Enter a code from your authenticator app to verify it's working.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        with st.form("verify_totp_form"):
            totp_code = st.text_input(
                "🔢 Enter 6-digit code",
                placeholder="000000",
                max_chars=6,
                help="Enter the 6-digit code from your authenticator app"
            )
            
            submit = st.form_submit_button(
                "✅ Verify Code",
                use_container_width=True,
                type="primary"
            )
            
            if submit:
                if not totp_code or len(totp_code) != 6:
                    st.error("❌ Please enter a valid 6-digit code")
                elif not totp_code.isdigit():
                    st.error("❌ Code must contain only numbers")
                else:
                    try:
                        if TOTPManager.verify_token(st.session_state.twofa_secret, totp_code):
                            st.success("✅ Code verified successfully!")
                            st.session_state.twofa_setup_step = "backup_codes"
                            logger.info(f"[2FA SETUP] TOTP verified for user {user_id}")
                            st.rerun()
                        else:
                            st.error("❌ Invalid code. Please try again.")
                            logger.warning(f"[2FA SETUP] Invalid TOTP code for user {user_id}")
                    except Exception as e:
                        st.error(f"❌ Error verifying code: {str(e)}")
                        logger.error(f"[2FA SETUP] Verification error: {str(e)}", exc_info=True)
        
        if st.button("⬅️ Cancel Setup", use_container_width=True):
            st.session_state.twofa_setup_step = "intro"
            st.session_state.twofa_secret = None
            st.session_state.twofa_backup_codes = None
            st.rerun()
    
    elif st.session_state.twofa_setup_step == "backup_codes":
        st.markdown("""
        <div class='success-box'>
            <h2 style='color: #155724; margin: 0;'>Step 3: Save Backup Codes</h2>
            <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>Save these codes in a secure location.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📋 Backup Codes")
        
        st.markdown("""
        <div class='warning-box'>
            <strong>⚠️ Important:</strong> Save these codes in a safe place! You can use them to log in if you lose access to your authenticator app.
            <br><br>
            Each code can only be used once. You have <strong>10 backup codes</strong>.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display backup codes
        st.markdown('<div class="backup-codes-box">', unsafe_allow_html=True)
        for code in st.session_state.twofa_backup_codes:
            st.markdown(f'<div class="backup-code">{code}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Download button
        codes_text = "\n".join(st.session_state.twofa_backup_codes)
        st.download_button(
            label="📥 Download Backup Codes",
            data=codes_text,
            file_name="2fa_backup_codes.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        st.markdown("---")
        
        with st.form("confirm_2fa_form"):
            confirmed = st.checkbox(
                "✅ I have saved my backup codes in a safe location",
                help="You must confirm before enabling 2FA"
            )
            
            submit = st.form_submit_button(
                "🔐 Enable Two-Factor Authentication",
                use_container_width=True,
                type="primary",
                disabled=not confirmed
            )
            
            if submit:
                try:
                    # Enable 2FA
                    update_user(
                        user_id,
                        two_factor_enabled=True,
                        two_factor_secret=st.session_state.twofa_secret,
                        backup_codes=st.session_state.twofa_backup_codes
                    )
                    
                    # Send confirmation email
                    user = get_user_by_id(user_id)
                    email_service.send_security_alert_email(
                        to_email=user.email,
                        user_name=user.name,
                        alert_message="Two-Factor Authentication has been enabled on your account.",
                        action_needed=False
                    )
                    
                    st.session_state.twofa_setup_step = "complete"
                    logger.info(f"[2FA SETUP] 2FA enabled for user {user_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error enabling 2FA: {str(e)}")
                    logger.error(f"[2FA SETUP] Error enabling 2FA: {str(e)}", exc_info=True)
    
    elif st.session_state.twofa_setup_step == "complete":
        st.markdown("""
        <div class='success-box'>
            <h2 style='color: #155724; margin: 0;'>✅ 2FA Successfully Enabled!</h2>
            <p style='color: #155724; font-size: 1.1rem; margin: 0.5rem 0;'>Your account is now protected with Two-Factor Authentication.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🎉 What's Next?")
        
        st.markdown("""
        <p class='info-text'>
        Your account is now more secure! When you log in next time, you'll need to verify with your authenticator app.
        </p>
        
        **Next steps:**
        - Log out and log back in to see 2FA in action
        - Keep your backup codes safe
        - If you lose your phone, use backup codes to log in
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⚙️ Back to Settings", use_container_width=True, type="primary"):
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
    <p>🔐 <strong>Two-Factor Authentication Setup</strong> | Secure your account</p>
    <p>Phase 2: 2FA setup | Using TOTP (Time-based One-Time Passwords)</p>
</div>
""", unsafe_allow_html=True)