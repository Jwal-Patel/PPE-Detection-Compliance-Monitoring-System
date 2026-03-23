"""
Auth package for user authentication, database models, and security utilities.
PHASE 2: Enhanced with email verification, password reset, 2FA, and activity logging.
"""

# ============================================================================
# MODELS - PHASE 1 & 2
# ============================================================================
from Auth.models import (
    # Phase 1 Models
    User,
    Organization,
    UserOrganization,
    Workstation,
    DetectionLog,
    Base,
    # Phase 2 Models
    EmailVerificationToken,
    PasswordResetToken,
    ActivityLog,
    AuditLog,
)

# ============================================================================
# DATABASE - PHASE 1 & 2
# ============================================================================
from Auth.db import (
    # Database Management
    init_db,
    get_db,
    SessionLocal,
    # Phase 1: User CRUD
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
    delete_user,
    # Phase 1: Organization CRUD
    create_organization,
    get_organization_by_id,
    get_organizations_by_user,
    update_organization,
    delete_organization,
    # Phase 1: User-Organization CRUD
    add_user_to_organization,
    remove_user_from_organization,
    get_organization_members,
    update_user_organization_role,
    # Phase 1: Workstation CRUD
    create_workstation,
    get_workstation_by_id,
    get_workstations_by_organization,
    update_workstation,
    delete_workstation,
    # Phase 1: Detection Logs
    create_detection_log,
    # Phase 2: Email Verification
    create_email_verification_token,
    get_user_by_email_verification_token,
    verify_email_token,
    # Phase 2: Password Reset
    create_password_reset_token,
    get_user_by_password_reset_token,
    verify_password_reset_token,
    use_password_reset_token,
    # Phase 2: Activity Logs
    create_activity_log,
    get_user_activity_logs,
    # Phase 2: Audit Logs
    create_audit_log,
    get_org_audit_logs,
)

# ============================================================================
# AUTHENTICATION - PHASE 1 & 2
# ============================================================================
from Auth.auth import (
    # Session Management
    init_session_state,
    is_authenticated,
    get_current_user_id,
    get_current_org_id,
    get_session_data,
    # Phase 1: Authentication
    login_user,
    logout_user,
    register_user,
    # Phase 1: Organization Management
    set_active_organization,
    get_user_organizations,
    get_user_full_info,
    # Phase 1: Authentication Guards
    require_auth,
    require_org_selected,
    require_admin_role,
    require_supervisor_or_admin,
    # Phase 2: Email Verification
    verify_email,
    resend_verification_email,
    # Phase 2: Password Reset
    request_password_reset,
    reset_password,
    # Phase 2: 2FA
    verify_2fa_token,
    verify_2fa_backup_code,
    # Phase 2: URL Helpers
    get_app_url,
    get_verification_link,
    get_password_reset_link,
)

# ============================================================================
# SECURITY - PHASE 1 & 2
# ============================================================================
from Auth.security import (
    # Password Management
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email_format,
    # Phase 2: Token Generation & Validation
    generate_secure_token,
    generate_verification_token,
    generate_password_reset_token,
    get_token_expiry,
    is_token_expired,
)

# ============================================================================
# 2FA/TOTP - PHASE 2
# ============================================================================
from Auth.totp import TOTPManager

# ============================================================================
# EMAIL SERVICE - PHASE 2
# ============================================================================
from Auth.email_service import email_service

# ============================================================================
# ALL EXPORTS
# ============================================================================

__all__ = [
    # ====================================================================
    # MODELS - PHASE 1
    # ====================================================================
    "User",
    "Organization",
    "UserOrganization",
    "Workstation",
    "DetectionLog",
    "Base",
    
    # ====================================================================
    # MODELS - PHASE 2
    # ====================================================================
    "EmailVerificationToken",
    "PasswordResetToken",
    "ActivityLog",
    "AuditLog",
    
    # ====================================================================
    # DATABASE - CORE
    # ====================================================================
    "init_db",
    "get_db",
    "SessionLocal",
    
    # ====================================================================
    # DATABASE - PHASE 1: USER CRUD
    # ====================================================================
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "update_user",
    "delete_user",
    
    # ====================================================================
    # DATABASE - PHASE 1: ORGANIZATION CRUD
    # ====================================================================
    "create_organization",
    "get_organization_by_id",
    "get_organizations_by_user",
    "update_organization",
    "delete_organization",
    
    # ====================================================================
    # DATABASE - PHASE 1: USER-ORGANIZATION CRUD
    # ====================================================================
    "add_user_to_organization",
    "remove_user_from_organization",
    "get_organization_members",
    "update_user_organization_role",
    
    # ====================================================================
    # DATABASE - PHASE 1: WORKSTATION CRUD
    # ====================================================================
    "create_workstation",
    "get_workstation_by_id",
    "get_workstations_by_organization",
    "update_workstation",
    "delete_workstation",
    
    # ====================================================================
    # DATABASE - PHASE 1: DETECTION LOGS
    # ====================================================================
    "create_detection_log",
    
    # ====================================================================
    # DATABASE - PHASE 2: EMAIL VERIFICATION
    # ====================================================================
    "create_email_verification_token",
    "get_user_by_email_verification_token",
    "verify_email_token",
    
    # ====================================================================
    # DATABASE - PHASE 2: PASSWORD RESET
    # ====================================================================
    "create_password_reset_token",
    "get_user_by_password_reset_token",
    "verify_password_reset_token",
    "use_password_reset_token",
    
    # ====================================================================
    # DATABASE - PHASE 2: ACTIVITY LOGS
    # ====================================================================
    "create_activity_log",
    "get_user_activity_logs",
    
    # ====================================================================
    # DATABASE - PHASE 2: AUDIT LOGS
    # ====================================================================
    "create_audit_log",
    "get_org_audit_logs",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 1: SESSION
    # ====================================================================
    "init_session_state",
    "is_authenticated",
    "get_current_user_id",
    "get_current_org_id",
    "get_session_data",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 1: LOGIN & LOGOUT
    # ====================================================================
    "login_user",
    "logout_user",
    "register_user",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 1: ORGANIZATION
    # ====================================================================
    "set_active_organization",
    "get_user_organizations",
    "get_user_full_info",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 1: GUARDS
    # ====================================================================
    "require_auth",
    "require_org_selected",
    "require_admin_role",
    "require_supervisor_or_admin",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 2: EMAIL VERIFICATION
    # ====================================================================
    "verify_email",
    "resend_verification_email",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 2: PASSWORD RESET
    # ====================================================================
    "request_password_reset",
    "reset_password",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 2: 2FA
    # ====================================================================
    "verify_2fa_token",
    "verify_2fa_backup_code",
    
    # ====================================================================
    # AUTHENTICATION - PHASE 2: URL HELPERS
    # ====================================================================
    "get_app_url",
    "get_verification_link",
    "get_password_reset_link",
    
    # ====================================================================
    # SECURITY - PHASE 1: PASSWORD
    # ====================================================================
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "validate_email_format",
    
    # ====================================================================
    # SECURITY - PHASE 2: TOKENS
    # ====================================================================
    "generate_secure_token",
    "generate_verification_token",
    "generate_password_reset_token",
    "get_token_expiry",
    "is_token_expired",
    
    # ====================================================================
    # 2FA/TOTP - PHASE 2
    # ====================================================================
    "TOTPManager",
    
    # ====================================================================
    # EMAIL SERVICE - PHASE 2
    # ====================================================================
    "email_service",
]

# ============================================================================
# VERSION INFORMATION
# ============================================================================

__version__ = "2.0.0"
__phase__ = "Phase 2.2"
__description__ = (
    "Enterprise PPE Detection & Compliance Platform\n"
    "Authentication: Email verification, password reset, 2FA (TOTP), activity logging"
)