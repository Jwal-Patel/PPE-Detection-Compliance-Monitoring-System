"""
High-level authentication logic for user registration, login, and session management.
Orchestrates database operations and security functions.
PHASE 2: Email verification, password reset, 2FA, and activity logging.
"""

from typing import Optional, Tuple, Dict
import streamlit as st
from datetime import datetime
import logging

from Auth.db import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    add_user_to_organization,
    get_organizations_by_user,
    update_user,
    # PHASE 2 imports
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    use_password_reset_token,
    create_activity_log,
    get_user_by_email_verification_token,
    get_user_by_password_reset_token,
)
from Auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email_format,
    # PHASE 2 imports
    generate_verification_token,
    generate_password_reset_token,
    get_token_expiry,
    is_token_expired,
)
from Auth.email_service import email_service
from Auth.totp import TOTPManager
from utils.config import (
    SESSION_USER_ID,
    SESSION_USER_EMAIL,
    SESSION_USER_NAME,
    SESSION_USER_ROLE,
    SESSION_ORG_ID,
    SESSION_ORG_NAME,
)

logger = logging.getLogger(__name__)


# ============================================================================
# URL HELPER FUNCTIONS
# ============================================================================

def get_app_url() -> str:
    """
    Get the current app URL dynamically.
    Works for localhost, deployed apps, and custom domains.
    
    Returns:
        Base URL of the application
    """
    try:
        # Get URL from Streamlit query params if available
        if hasattr(st, 'query_params') and 'app_url' in st.query_params:
            return st.query_params['app_url']
        
        # Try to get from environment or config
        import os
        app_url = os.getenv("APP_URL", "").strip()
        if app_url:
            return app_url.rstrip('/')
        
        # Default to localhost for development
        return "http://localhost:8501"
    except:
        return "http://localhost:8501"


def get_verification_link(token: str) -> str:
    """
    Generate email verification link with correct app URL.
    
    Args:
        token: Verification token
        
    Returns:
        Full verification URL
    """
    app_url = get_app_url()
    # FIXED: Use correct Streamlit page path format (without pages/ prefix and .py)
    return f"{app_url}/Verify_Email?token={token}"


def get_password_reset_link(token: str) -> str:
    """
    Generate password reset link with correct app URL.
    
    Args:
        token: Reset token
        
    Returns:
        Full password reset URL
    """
    app_url = get_app_url()
    # FIXED: Use correct Streamlit page path format (without pages/ prefix and .py)
    return f"{app_url}/Reset_Password?token={token}"


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def init_session_state() -> None:
    """
    Initialize Streamlit session state with required keys.
    Called once per app startup.
    PHASE 2: Added 2FA and verification tracking.
    """
    if SESSION_USER_ID not in st.session_state:
        st.session_state[SESSION_USER_ID] = None
    
    if SESSION_USER_EMAIL not in st.session_state:
        st.session_state[SESSION_USER_EMAIL] = None
    
    if SESSION_USER_NAME not in st.session_state:
        st.session_state[SESSION_USER_NAME] = None
    
    if SESSION_USER_ROLE not in st.session_state:
        st.session_state[SESSION_USER_ROLE] = None
    
    if SESSION_ORG_ID not in st.session_state:
        st.session_state[SESSION_ORG_ID] = None
    
    if SESSION_ORG_NAME not in st.session_state:
        st.session_state[SESSION_ORG_NAME] = None
    
    # PHASE 2: Session tracking
    if "login_time" not in st.session_state:
        st.session_state["login_time"] = None
    
    if "2fa_pending" not in st.session_state:
        st.session_state["2fa_pending"] = False
    
    if "2fa_user_id" not in st.session_state:
        st.session_state["2fa_user_id"] = None


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    
    Returns:
        True if user_id exists in session, False otherwise
    """
    return st.session_state.get(SESSION_USER_ID) is not None


def get_current_user_id() -> Optional[int]:
    """
    Get the currently logged-in user's ID.
    
    Returns:
        User ID if authenticated, None otherwise
    """
    return st.session_state.get(SESSION_USER_ID)


def get_current_org_id() -> Optional[int]:
    """
    Get the currently selected organization ID.
    
    Returns:
        Organization ID if set, None otherwise
    """
    return st.session_state.get(SESSION_ORG_ID)


def get_session_data() -> Dict:
    """
    Get all current session data.
    
    Returns:
        Dictionary containing all session information
    """
    return {
        "user_id": st.session_state.get(SESSION_USER_ID),
        "email": st.session_state.get(SESSION_USER_EMAIL),
        "name": st.session_state.get(SESSION_USER_NAME),
        "role": st.session_state.get(SESSION_USER_ROLE),
        "org_id": st.session_state.get(SESSION_ORG_ID),
        "org_name": st.session_state.get(SESSION_ORG_NAME),
        "login_time": st.session_state.get("login_time"),
    }


# ============================================================================
# USER REGISTRATION WITH EMAIL VERIFICATION (PHASE 2)
# ============================================================================
def register_user(
    email: str,
    password: str,
    confirm_password: str,
    name: str
) -> Tuple[bool, str]:
    """
    Register a new user account with email verification.
    
    PHASE 2: User registration now requires email verification before activation.
    
    Args:
        email: User's email address
        password: User's password
        confirm_password: Password confirmation
        name: User's full name
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    # Step 1: Validate email format
    email_valid, email_msg = validate_email_format(email.strip())
    if not email_valid:
        return False, email_msg
    
    # Step 2: Validate password strength
    pwd_valid, pwd_msg = validate_password_strength(password)
    if not pwd_valid:
        return False, pwd_msg
    
    # Step 3: Check passwords match
    if password != confirm_password:
        return False, "Passwords do not match"
    
    # Step 4: Validate name
    if not name or len(name.strip()) == 0:
        return False, "Name cannot be empty"
    
    if len(name) > 255:
        return False, "Name is too long (max 255 characters)"
    
    # Step 5: Check if email already exists
    existing_user = get_user_by_email(email.strip())
    if existing_user:
        return False, "Email already registered. Please login or use a different email."
    
    # Step 6: Hash password and create user
    try:
        password_hash = hash_password(password)
        new_user = create_user(
            email=email.strip(),
            password_hash=password_hash,
            name=name.strip(),
            role="Viewer",
            email_verified=False  # PHASE 2: Email not yet verified
        )
        
        if new_user:
            # PHASE 2: Create and send verification email
            token = generate_verification_token()
            verification_link = get_verification_link(token)
            
            token_created = create_email_verification_token(
                user_id=new_user.id,
                token=token,
                email=email.strip()
            )
            
            if token_created and email_service.send_verification_email(
                to_email=email.strip(),
                user_name=name.strip(),
                verification_link=verification_link
            ):
                return True, "Registration successful! Please check your email to verify your account."
            else:
                return True, "Registration successful! Please check your email (or spam folder) to verify your account."
        else:
            return False, "Registration failed. Please try again."
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return False, f"Registration error: {str(e)}"


# ============================================================================
# EMAIL VERIFICATION (PHASE 2)
# ============================================================================

def verify_email(token: str) -> Tuple[bool, str]:
    """
    Verify user's email address using verification token.
    
    PHASE 2: New feature for email verification.
    
    Args:
        token: Email verification token
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Get user by token (only unverified tokens)
        user = get_user_by_email_verification_token(token)
        if not user:
            return False, "Invalid or expired verification link."
        
        # Verify and mark token as verified
        verified = verify_email_token(token)
        if verified:
            # Update user email_verified status
            update_user(
                user.id,
                email_verified=True,
                email_verified_at=datetime.utcnow()
            )
            logger.info(f"Email verified for user {user.id} ({user.email})")
            return True, "✅ Email verified successfully! You can now log in."
        else:
            logger.warning(f"Email verification failed for token (already used or expired)")
            return False, "Invalid or expired verification link."
    
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        return False, "An error occurred during verification."


def resend_verification_email(email: str) -> Tuple[bool, str]:
    """
    Resend verification email to user.
    
    PHASE 2: New feature for resending verification emails.
    
    Args:
        email: User's email address
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        user = get_user_by_email(email.strip())
        if not user:
            return False, "Email not found."
        
        if user.email_verified:
            return False, "Email is already verified."
        
        token = generate_verification_token()
        verification_link = get_verification_link(token)
        
        token_created = create_email_verification_token(
            user_id=user.id,
            token=token,
            email=email.strip()
        )
        
        if token_created and email_service.send_verification_email(
            to_email=email.strip(),
            user_name=user.name,
            verification_link=verification_link
        ):
            return True, "Verification email sent! Please check your email."
        else:
            return False, "Failed to send verification email. Please try again."
    
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return False, "An error occurred."


# ============================================================================
# USER LOGIN WITH 2FA SUPPORT (PHASE 2)
# ============================================================================

def login_user(email: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate a user and create a session.
    
    PHASE 2: Enhanced with email verification requirement and 2FA support.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    # Step 1: Validate email format
    email_valid, email_msg = validate_email_format(email.strip())
    if not email_valid:
        return False, "Invalid email format"
    
    # Step 2: Find user by email
    user = get_user_by_email(email.strip())
    if not user:
        return False, "Email not found. Please register first."
    
    # Step 3: Check if account is active
    if not user.is_active:
        return False, "Account is inactive. Please contact support."
    
    # PHASE 2: Check if email is verified
    if not user.email_verified:
        return False, "Please verify your email before logging in. Check your email for the verification link."
    
    # Step 4: Verify password
    if not verify_password(password, user.password_hash):
        # Log failed attempt
        failed_attempts = (user.failed_login_attempts or 0) + 1
        update_user(user.id, failed_login_attempts=failed_attempts)
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            update_user(user.id, account_locked_until=get_token_expiry(hours=1))
            return False, "Account locked due to too many failed attempts. Try again in 1 hour."
        
        return False, f"Incorrect password. {5 - failed_attempts} attempts remaining."
    
    # Check if account is locked
    if user.account_locked_until and not is_token_expired(user.account_locked_until):
        return False, "Account is locked. Please try again later."
    
    # Reset failed login attempts
    update_user(user.id, failed_login_attempts=0, account_locked_until=None)
    
    # PHASE 2: Check if 2FA is enabled
    if user.two_factor_enabled:
        st.session_state["2fa_pending"] = True
        st.session_state["2fa_user_id"] = user.id
        return True, "2FA_REQUIRED"  # Special message indicating 2FA is needed
    
    # Step 5: Create session
    try:
        st.session_state[SESSION_USER_ID] = user.id
        st.session_state[SESSION_USER_EMAIL] = user.email
        st.session_state[SESSION_USER_NAME] = user.name
        st.session_state[SESSION_USER_ROLE] = user.role
        st.session_state["login_time"] = datetime.utcnow()
        
        # Log activity
        create_activity_log(
            user_id=user.id,
            action="login",
            description="User logged in successfully",
            ip_address=None  # Get from request if available
        )
        
        # Auto-select first organization if user has any
        user_orgs = get_organizations_by_user(user.id)
        if user_orgs:
            st.session_state[SESSION_ORG_ID] = user_orgs[0].id
            st.session_state[SESSION_ORG_NAME] = user_orgs[0].name
        
        # Update last login
        update_user(user.id, last_login=datetime.utcnow())
        
        return True, f"Welcome back, {user.name}!"
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False, f"Login error: {str(e)}"


# ============================================================================
# 2FA VERIFICATION (PHASE 2)
# ============================================================================

def verify_2fa_token(token: str) -> Tuple[bool, str]:
    """
    Verify 2FA TOTP token and complete login.
    
    PHASE 2: New feature for 2FA authentication.
    
    Args:
        token: 6-digit TOTP code from authenticator app
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not st.session_state.get("2fa_pending"):
        return False, "No 2FA verification in progress."
    
    user_id = st.session_state.get("2fa_user_id")
    if not user_id:
        return False, "Session error. Please log in again."
    
    try:
        user = get_user_by_id(user_id)
        if not user or not user.two_factor_enabled:
            return False, "2FA is not enabled for this account."
        
        # Verify TOTP token
        if TOTPManager.verify_token(user.two_factor_secret, token):
            # 2FA successful - complete login
            st.session_state[SESSION_USER_ID] = user.id
            st.session_state[SESSION_USER_EMAIL] = user.email
            st.session_state[SESSION_USER_NAME] = user.name
            st.session_state[SESSION_USER_ROLE] = user.role
            st.session_state["login_time"] = datetime.utcnow()
            st.session_state["2fa_pending"] = False
            st.session_state["2fa_user_id"] = None
            
            # Log activity
            create_activity_log(
                user_id=user.id,
                action="2fa_verified",
                description="2FA authentication successful",
            )
            
            return True, "2FA verified successfully!"
        else:
            return False, "Invalid TOTP code. Please try again."
    
    except Exception as e:
        logger.error(f"2FA verification error: {str(e)}")
        return False, "An error occurred during 2FA verification."


def verify_2fa_backup_code(code: str) -> Tuple[bool, str]:
    """
    Verify 2FA backup code and complete login.
    
    PHASE 2: New feature for 2FA backup codes.
    
    Args:
        code: Backup code
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not st.session_state.get("2fa_pending"):
        return False, "No 2FA verification in progress."
    
    user_id = st.session_state.get("2fa_user_id")
    if not user_id:
        return False, "Session error. Please log in again."
    
    try:
        user = get_user_by_id(user_id)
        if not user or not user.two_factor_enabled:
            return False, "2FA is not enabled for this account."
        
        # Verify backup code
        backup_codes = user.backup_codes or []
        is_valid, remaining_codes = TOTPManager.use_backup_code(backup_codes, code.strip())
        
        if is_valid:
            # Update backup codes
            update_user(user.id, backup_codes=remaining_codes)
            
            # Complete login
            st.session_state[SESSION_USER_ID] = user.id
            st.session_state[SESSION_USER_EMAIL] = user.email
            st.session_state[SESSION_USER_NAME] = user.name
            st.session_state[SESSION_USER_ROLE] = user.role
            st.session_state["login_time"] = datetime.utcnow()
            st.session_state["2fa_pending"] = False
            st.session_state["2fa_user_id"] = None
            
            # Log activity
            create_activity_log(
                user_id=user.id,
                action="backup_code_used",
                description=f"Backup code used for 2FA. {len(remaining_codes)} codes remaining.",
            )
            
            return True, "Login successful! Note: You used a backup code. Generate new ones in Settings."
        else:
            return False, "Invalid backup code."
    
    except Exception as e:
        logger.error(f"Backup code verification error: {str(e)}")
        return False, "An error occurred."


# ============================================================================
# PASSWORD RESET (PHASE 2)
# ============================================================================

def request_password_reset(email: str) -> Tuple[bool, str]:
    """
    Request password reset for user account.
    
    PHASE 2: New feature for password reset functionality.
    
    Args:
        email: User's email address
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        user = get_user_by_email(email.strip())
        if not user:
            # Don't reveal if email exists for security
            return True, "If an account exists with this email, you will receive a password reset link."
        
        # Generate reset token
        token = generate_password_reset_token()
        reset_link = get_password_reset_link(token)
        
        token_created = create_password_reset_token(
            user_id=user.id,
            token=token,
            expires_at=get_token_expiry(hours=1)  # 1 hour expiry
        )
        
        if token_created:
            email_service.send_password_reset_email(
                to_email=user.email,
                user_name=user.name,
                reset_link=reset_link
            )
            
            # Log activity
            create_activity_log(
                user_id=user.id,
                action="password_reset_requested",
                description="Password reset requested",
            )
        
        return True, "If an account exists with this email, you will receive a password reset link."
    
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return True, "If an account exists with this email, you will receive a password reset link."


def reset_password(token: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
    """
    Reset user password using reset token.
    
    PHASE 2: New feature for password reset functionality.
    
    Args:
        token: Password reset token
        new_password: New password
        confirm_password: Password confirmation
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Validate passwords
        if new_password != confirm_password:
            return False, "Passwords do not match."
        
        pwd_valid, pwd_msg = validate_password_strength(new_password)
        if not pwd_valid:
            return False, pwd_msg
        
        # Verify token
        user = get_user_by_password_reset_token(token)
        if not user:
            return False, "Invalid or expired reset link."
        
        if not verify_password_reset_token(token):
            return False, "Invalid or expired reset link."
        
        # Update password
        new_hash = hash_password(new_password)
        updated = use_password_reset_token(token, new_hash)
        
        if updated:
            # Log activity
            create_activity_log(
                user_id=user.id,
                action="password_changed",
                description="Password changed via reset link",
            )
            
            # Send confirmation email
            email_service.send_security_alert_email(
                to_email=user.email,
                user_name=user.name,
                alert_message="Your password was successfully changed.",
                action_needed=False
            )
            
            return True, "✅ Password reset successful! You can now log in with your new password."
        else:
            return False, "Failed to reset password. Please try again."
    
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return False, "An error occurred during password reset."


# ============================================================================
# USER LOGOUT
# ============================================================================

def logout_user() -> None:
    """
    Clear user session and logout.
    
    PHASE 2: Added activity logging.
    """
    user_id = st.session_state.get(SESSION_USER_ID)
    
    if user_id:
        # Log logout activity
        create_activity_log(
            user_id=user_id,
            action="logout",
            description="User logged out",
        )
    
    st.session_state[SESSION_USER_ID] = None
    st.session_state[SESSION_USER_EMAIL] = None
    st.session_state[SESSION_USER_NAME] = None
    st.session_state[SESSION_USER_ROLE] = None
    st.session_state[SESSION_ORG_ID] = None
    st.session_state[SESSION_ORG_NAME] = None
    st.session_state["login_time"] = None
    st.session_state["2fa_pending"] = False
    st.session_state["2fa_user_id"] = None


# ============================================================================
# AUTHENTICATION GUARDS
# ============================================================================

def require_auth() -> bool:
    """
    Guard function to ensure user is authenticated.
    
    Returns:
        True if user is authenticated, False otherwise
    """
    if not is_authenticated():
        st.warning("⚠️ Please log in to access this page.")
        st.info("Navigate to the **🔐 Account** page to log in or register.")
        return False
    
    return True


def require_org_selected() -> bool:
    """
    Guard function to ensure user has selected an organization.
    
    Returns:
        True if organization is selected, False otherwise
    """
    if not is_authenticated():
        return False
    
    if get_current_org_id() is None:
        st.warning("⚠️ Please select or create an organization first.")
        st.info("Navigate to the **🏢 Organizations** page to create one.")
        return False
    
    return True


def require_admin_role() -> bool:
    """
    Guard function to ensure user has admin role.
    
    Returns:
        True if user is admin, False otherwise
    """
    if not is_authenticated():
        return False
    
    user_role = st.session_state.get(SESSION_USER_ROLE)
    if user_role != "Admin":
        st.error("❌ Admin access required.")
        return False
    
    return True


def require_supervisor_or_admin() -> bool:
    """
    Guard function to ensure user has supervisor or admin role.
    
    Returns:
        True if user is supervisor or admin, False otherwise
    """
    if not is_authenticated():
        return False
    
    user_role = st.session_state.get(SESSION_USER_ROLE)
    if user_role not in ["Admin", "Supervisor"]:
        st.error("❌ Supervisor access required.")
        return False
    
    return True


# ============================================================================
# SESSION & ORGANIZATION MANAGEMENT
# ============================================================================

def set_active_organization(org_id: int, org_name: str) -> None:
    """
    Set the active organization in session.
    
    Args:
        org_id: Organization ID to activate
        org_name: Organization name
    """
    st.session_state[SESSION_ORG_ID] = org_id
    st.session_state[SESSION_ORG_NAME] = org_name


def get_user_organizations() -> list:
    """
    Get all organizations the current user belongs to.
    
    Returns:
        List of Organization objects
    """
    user_id = get_current_user_id()
    if not user_id:
        return []
    
    return get_organizations_by_user(user_id)


def get_user_full_info():
    """
    Get complete user information from database.
    
    Returns:
        User object if authenticated, None otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        return None
    
    return get_user_by_id(user_id)