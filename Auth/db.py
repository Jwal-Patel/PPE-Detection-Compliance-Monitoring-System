"""
Database initialization, session management, and CRUD operations.
Handles all database interactions using SQLAlchemy ORM.
PHASE 2: Enhanced with email verification, password reset, 2FA, and activity logging.
"""

from typing import Optional, List, Dict, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
import logging

from utils.config import DATABASE_URL, SQLALCHEMY_ECHO
from Auth.models import (
    Base, User, Organization, UserOrganization, Workstation, DetectionLog,
    # PHASE 2 models
    EmailVerificationToken, PasswordResetToken, ActivityLog, AuditLog
)
from Auth.security import is_token_expired

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE & SESSION FACTORY
# ============================================================================

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Initialize the database by creating all tables defined in models.
    Safe to call multiple times - only creates missing tables.
    PHASE 2: Creates Phase 2 tables (EmailVerificationToken, PasswordResetToken, ActivityLog, AuditLog)
    
    Raises:
        SQLAlchemyError: If database creation fails
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise SQLAlchemyError(f"Failed to initialize database: {str(e)}")


def get_db() -> Session:
    """
    Get a database session for use in Streamlit pages.
    
    Yields:
        SQLAlchemy Session object
        
    Example:
        >>> for db in get_db():
        ...     user = db.query(User).filter_by(email="user@example.com").first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# USER CRUD OPERATIONS
# ============================================================================

def create_user(
    email: str,
    password_hash: str,
    name: str,
    role: str = "Viewer",
    email_verified: bool = False  # PHASE 2
) -> Optional[User]:
    """
    Create a new user in the database.
    
    Args:
        email: User's email address (must be unique)
        password_hash: Bcrypt hashed password
        name: User's full name
        role: User role (Admin, Supervisor, Viewer)
        email_verified: Whether email is verified (PHASE 2)
        
    Returns:
        Created User object or None if creation failed
        
    Raises:
        IntegrityError: If email already exists
    """
    db = SessionLocal()
    try:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            is_active=True,
            email_verified=email_verified  # PHASE 2
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created: {email}")
        return user
    except IntegrityError:
        db.rollback()
        logger.warning(f"User creation failed - email already exists: {email}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise SQLAlchemyError(f"Failed to create user: {str(e)}")
    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by email address.
    
    Args:
        email: Email address to search for
        
    Returns:
        User object if found, None otherwise
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve user by email: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve user: {str(e)}")
    finally:
        db.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    
    Args:
        user_id: User ID to search for
        
    Returns:
        User object if found, None otherwise
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve user by ID: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve user: {str(e)}")
    finally:
        db.close()


def update_user(user_id: int, **kwargs) -> Optional[User]:
    """
    Update user attributes.
    
    Args:
        user_id: ID of user to update
        **kwargs: Fields to update (name, email, role, is_active, email_verified, etc.)
        
    Returns:
        Updated User object or None if not found
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        logger.info(f"User updated: {user.email}")
        return user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update user: {str(e)}")
        raise SQLAlchemyError(f"Failed to update user: {str(e)}")
    finally:
        db.close()


def delete_user(user_id: int) -> bool:
    """
    Delete a user from the database.
    
    Args:
        user_id: ID of user to delete
        
    Returns:
        True if deleted, False if not found
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        email = user.email
        db.delete(user)
        db.commit()
        logger.info(f"User deleted: {email}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete user: {str(e)}")
        raise SQLAlchemyError(f"Failed to delete user: {str(e)}")
    finally:
        db.close()


# ============================================================================
# ORGANIZATION CRUD OPERATIONS
# ============================================================================

def create_organization(
    name: str,
    admin_user_id: int,
    description: Optional[str] = None
) -> Optional[Organization]:
    """
    Create a new organization.
    
    Args:
        name: Organization name (must be unique)
        admin_user_id: ID of admin user
        description: Optional description
        
    Returns:
        Created Organization object or None if creation failed
    """
    db = SessionLocal()
    try:
        org = Organization(
            name=name,
            admin_user_id=admin_user_id,
            description=description
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info(f"Organization created: {name}")
        return org
    except IntegrityError:
        db.rollback()
        logger.warning(f"Organization creation failed - name already exists: {name}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to create organization: {str(e)}")
    finally:
        db.close()


def get_organization_by_id(org_id: int) -> Optional[Organization]:
    """
    Retrieve an organization by ID.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Organization object if found, None otherwise
    """
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        return org
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve organization: {str(e)}")
    finally:
        db.close()


def get_organizations_by_user(user_id: int) -> List[Organization]:
    """
    Get all organizations a user is a member of.
    
    Args:
        user_id: User ID
        
    Returns:
        List of Organization objects with all relationships loaded
    """
    from sqlalchemy.orm import joinedload
    
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    try:
        user_orgs = db.query(UserOrganization).filter(UserOrganization.user_id == user_id).all()
        return [uo.organization for uo in user_orgs]
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve organizations: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve organizations: {str(e)}")
    finally:
        db.close()


def get_organizations_by_user_with_details(user_id: int) -> List[Dict]:
    """
    Get all organizations a user is a member of with full details.
    
    ✅ SOLUTION: Returns dictionaries instead of ORM objects to avoid DetachedInstanceError.
    This is the RECOMMENDED approach for Streamlit pages.
    
    Args:
        user_id: User ID
        
    Returns:
        List of dictionaries with organization details
    """
    db = SessionLocal()
    try:
        user_orgs = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id
        ).all()
        
        organizations_data = []
        for uo in user_orgs:
            org = uo.organization
            organizations_data.append({
                'id': org.id,
                'name': org.name,
                'description': org.description,
                'admin_user_id': org.admin_user_id,
                'created_at': org.created_at,
                'updated_at': org.updated_at,
                'member_count': len(org.user_organizations) if org.user_organizations else 0,
                'workstation_count': len(org.workstations) if org.workstations else 0,
                'user_role': uo.role,
            })
        
        logger.info(f"Retrieved {len(organizations_data)} organizations for user {user_id}")
        return organizations_data
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve organizations: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve organizations: {str(e)}")
    finally:
        db.close()


def update_organization(org_id: int, **kwargs) -> Optional[Organization]:
    """
    Update organization attributes.
    
    Args:
        org_id: Organization ID
        **kwargs: Fields to update (name, description, etc.)
        
    Returns:
        Updated Organization object or None if not found
    """
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return None
        
        for key, value in kwargs.items():
            if hasattr(org, key):
                setattr(org, key, value)
        
        db.commit()
        db.refresh(org)
        logger.info(f"Organization updated: {org.name}")
        return org
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to update organization: {str(e)}")
    finally:
        db.close()


def delete_organization(org_id: int) -> bool:
    """
    Delete an organization (cascades to related records).
    
    Args:
        org_id: Organization ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return False
        
        org_name = org.name
        db.delete(org)
        db.commit()
        logger.info(f"Organization deleted: {org_name}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to delete organization: {str(e)}")
    finally:
        db.close()


# ============================================================================
# USER-ORGANIZATION CRUD OPERATIONS
# ============================================================================

def add_user_to_organization(
    user_id: int,
    org_id: int,
    role: str = "Viewer"
) -> Optional[UserOrganization]:
    """
    Add a user to an organization with a specific role.
    
    Args:
        user_id: User ID
        org_id: Organization ID
        role: Role in organization (Admin, Supervisor, Viewer)
        
    Returns:
        Created UserOrganization object or None if creation failed
    """
    db = SessionLocal()
    try:
        user_org = UserOrganization(
            user_id=user_id,
            org_id=org_id,
            role=role
        )
        db.add(user_org)
        db.commit()
        db.refresh(user_org)
        logger.info(f"User {user_id} added to organization {org_id} with role {role}")
        return user_org
    except IntegrityError:
        db.rollback()
        logger.warning(f"User already in organization")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to add user to organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to add user to organization: {str(e)}")
    finally:
        db.close()


def remove_user_from_organization(user_id: int, org_id: int) -> bool:
    """
    Remove a user from an organization.
    
    Args:
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        True if removed, False if record not found
    """
    db = SessionLocal()
    try:
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.org_id == org_id
        ).first()
        
        if not user_org:
            return False
        
        db.delete(user_org)
        db.commit()
        logger.info(f"User {user_id} removed from organization {org_id}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to remove user from organization: {str(e)}")
        raise SQLAlchemyError(f"Failed to remove user from organization: {str(e)}")
    finally:
        db.close()


def get_organization_members(org_id: int) -> List[UserOrganization]:
    """
    Get all members of an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        List of UserOrganization objects
    """
    db = SessionLocal()
    try:
        members = db.query(UserOrganization).filter(UserOrganization.org_id == org_id).all()
        return members
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve organization members: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve organization members: {str(e)}")
    finally:
        db.close()


def update_user_organization_role(user_id: int, org_id: int, role: str) -> Optional[UserOrganization]:
    """
    Update a user's role within an organization.
    
    Args:
        user_id: User ID
        org_id: Organization ID
        role: New role (Admin, Supervisor, Viewer)
        
    Returns:
        Updated UserOrganization object or None if not found
    """
    db = SessionLocal()
    try:
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.org_id == org_id
        ).first()
        
        if not user_org:
            return None
        
        user_org.role = role
        db.commit()
        db.refresh(user_org)
        logger.info(f"User {user_id} role updated to {role} in organization {org_id}")
        return user_org
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update user organization role: {str(e)}")
        raise SQLAlchemyError(f"Failed to update user organization role: {str(e)}")
    finally:
        db.close()


# ============================================================================
# WORKSTATION CRUD OPERATIONS
# ============================================================================

def create_workstation(
    org_id: int,
    name: str,
    camera_url: Optional[str] = None,
    description: Optional[str] = None,
    ppe_model_path: Optional[str] = None
) -> Optional[Workstation]:
    """
    Create a new workstation.
    
    Args:
        org_id: Organization ID
        name: Workstation name
        camera_url: Optional camera stream URL
        description: Optional description
        ppe_model_path: Optional path to PPE model weights
        
    Returns:
        Created Workstation object or None if creation failed
    """
    db = SessionLocal()
    try:
        workstation = Workstation(
            org_id=org_id,
            name=name,
            camera_url=camera_url,
            description=description,
            ppe_model_path=ppe_model_path,
            is_active=True
        )
        db.add(workstation)
        db.commit()
        db.refresh(workstation)
        logger.info(f"Workstation created: {name}")
        return workstation
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create workstation: {str(e)}")
        raise SQLAlchemyError(f"Failed to create workstation: {str(e)}")
    finally:
        db.close()


def get_workstation_by_id(workstation_id: int) -> Optional[Workstation]:
    """
    Retrieve a workstation by ID.
    
    Args:
        workstation_id: Workstation ID
        
    Returns:
        Workstation object if found, None otherwise
    """
    db = SessionLocal()
    try:
        workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
        return workstation
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve workstation: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve workstation: {str(e)}")
    finally:
        db.close()


def get_workstations_by_organization(org_id: int) -> List[Workstation]:
    """
    Get all workstations for an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        List of Workstation objects
    """
    db = SessionLocal()
    try:
        workstations = db.query(Workstation).filter(Workstation.org_id == org_id).all()
        return workstations
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve workstations: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve workstations: {str(e)}")
    finally:
        db.close()


def update_workstation(workstation_id: int, **kwargs) -> Optional[Workstation]:
    """
    Update workstation attributes.
    
    Args:
        workstation_id: Workstation ID
        **kwargs: Fields to update (name, camera_url, is_active, etc.)
        
    Returns:
        Updated Workstation object or None if not found
    """
    db = SessionLocal()
    try:
        workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
        if not workstation:
            return None
        
        for key, value in kwargs.items():
            if hasattr(workstation, key):
                setattr(workstation, key, value)
        
        db.commit()
        db.refresh(workstation)
        logger.info(f"Workstation updated: {workstation.name}")
        return workstation
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update workstation: {str(e)}")
        raise SQLAlchemyError(f"Failed to update workstation: {str(e)}")
    finally:
        db.close()


def delete_workstation(workstation_id: int) -> bool:
    """
    Delete a workstation.
    
    Args:
        workstation_id: Workstation ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    db = SessionLocal()
    try:
        workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
        if not workstation:
            return False
        
        ws_name = workstation.name
        db.delete(workstation)
        db.commit()
        logger.info(f"Workstation deleted: {ws_name}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete workstation: {str(e)}")
        raise SQLAlchemyError(f"Failed to delete workstation: {str(e)}")
    finally:
        db.close()


# ============================================================================
# DETECTION LOG CRUD OPERATIONS
# ============================================================================

def create_detection_log(
    workstation_id: int,
    frame_timestamp: datetime,
    worker_count: int,
    compliant_count: int,
    partial_count: int,
    non_compliant_count: int,
    ppe_breakdown: Dict,
    raw_detections: str
) -> Optional[DetectionLog]:
    """
    Create a new detection log entry.
    
    Args:
        workstation_id: Workstation ID
        frame_timestamp: Detection timestamp
        worker_count: Total workers detected
        compliant_count: Compliant workers count
        partial_count: Partial compliance workers count
        non_compliant_count: Non-compliant workers count
        ppe_breakdown: PPE breakdown dictionary
        raw_detections: Raw detection JSON string
        
    Returns:
        Created DetectionLog or None if failed
    """
    db = SessionLocal()
    try:
        log = DetectionLog(
            workstation_id=workstation_id,
            frame_timestamp=frame_timestamp,
            worker_count=worker_count,
            compliant_count=compliant_count,
            partial_count=partial_count,
            non_compliant_count=non_compliant_count,
            ppe_breakdown=ppe_breakdown,
            raw_detections=raw_detections
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        logger.info(f"Detection log created for workstation {workstation_id}")
        return log
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create detection log: {str(e)}")
        raise SQLAlchemyError(f"Failed to create detection log: {str(e)}")
    finally:
        db.close()


# ============================================================================
# PHASE 2: EMAIL VERIFICATION TOKEN OPERATIONS
# ============================================================================

def create_email_verification_token(
    user_id: int,
    token: str,
    email: str,
    expires_hours: int = 24
) -> Optional[EmailVerificationToken]:
    """
    Create an email verification token.
    
    PHASE 2: New feature for email verification.
    
    Args:
        user_id: User ID
        token: Verification token
        email: Email address to verify
        expires_hours: Token expiry in hours (default: 24)
        
    Returns:
        Created EmailVerificationToken or None
    """
    db = SessionLocal()
    try:
        from Auth.security import get_token_expiry
        
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            email=email,
            expires_at=get_token_expiry(hours=expires_hours)
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        logger.info(f"Email verification token created for user {user_id}")
        return verification_token
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create email verification token: {str(e)}")
        raise SQLAlchemyError(f"Failed to create email verification token: {str(e)}")
    finally:
        db.close()


def get_user_by_email_verification_token(token: str) -> Optional[User]:
    """
    Get user by email verification token.
    Handles both verified and unverified tokens.
    
    PHASE 2: New feature for email verification.
    
    Args:
        token: Email verification token
        
    Returns:
        User object or None if token invalid/expired
    """
    db = SessionLocal()
    try:
        # Find token (both verified and unverified)
        verification_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()
        
        # Check if token exists and is not expired
        if verification_token and not is_token_expired(verification_token.expires_at):
            user = db.query(User).filter(User.id == verification_token.user_id).first()
            return user
        
        return None
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve user by verification token: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve user by verification token: {str(e)}")
    finally:
        db.close()


def verify_email_token(token: str) -> bool:
    """
    Mark email verification token as verified.
    
    PHASE 2: New feature for email verification.
    
    Args:
        token: Email verification token
        
    Returns:
        True if verified successfully, False otherwise
    """
    db = SessionLocal()
    try:
        verification_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.verified == False
        ).first()
        
        if verification_token and not is_token_expired(verification_token.expires_at):
            verification_token.verified = True
            verification_token.verified_at = datetime.utcnow()
            db.commit()
            logger.info(f"Email verified for token")
            return True
        logger.warning(f"Email verification token invalid or expired")
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to verify email token: {str(e)}")
        raise SQLAlchemyError(f"Failed to verify email token: {str(e)}")
    finally:
        db.close()


# ============================================================================
# PHASE 2: PASSWORD RESET TOKEN OPERATIONS
# ============================================================================

def create_password_reset_token(
    user_id: int,
    token: str,
    expires_at: datetime
) -> Optional[PasswordResetToken]:
    """
    Create a password reset token.
    
    PHASE 2: New feature for password reset.
    
    Args:
        user_id: User ID
        token: Reset token
        expires_at: Token expiry datetime
        
    Returns:
        Created PasswordResetToken or None
    """
    db = SessionLocal()
    try:
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)
        logger.info(f"Password reset token created for user {user_id}")
        return reset_token
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create password reset token: {str(e)}")
        raise SQLAlchemyError(f"Failed to create password reset token: {str(e)}")
    finally:
        db.close()


def get_user_by_password_reset_token(token: str) -> Optional[User]:
    """
    Get user by password reset token.
    
    PHASE 2: New feature for password reset.
    
    Args:
        token: Password reset token
        
    Returns:
        User object or None if token invalid/expired
    """
    db = SessionLocal()
    try:
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False
        ).first()
        
        if reset_token and not is_token_expired(reset_token.expires_at):
            return reset_token.user
        return None
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve user by reset token: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve user by reset token: {str(e)}")
    finally:
        db.close()


def verify_password_reset_token(token: str) -> bool:
    """
    Verify password reset token is still valid.
    
    PHASE 2: New feature for password reset.
    
    Args:
        token: Password reset token
        
    Returns:
        True if token is valid, False otherwise
    """
    db = SessionLocal()
    try:
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False
        ).first()
        
        if reset_token and not is_token_expired(reset_token.expires_at):
            return True
        logger.warning(f"Password reset token invalid or expired")
        return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to verify reset token: {str(e)}")
        raise SQLAlchemyError(f"Failed to verify reset token: {str(e)}")
    finally:
        db.close()


def use_password_reset_token(token: str, new_password_hash: str) -> bool:
    """
    Use password reset token and update password.
    
    PHASE 2: New feature for password reset.
    
    Args:
        token: Password reset token
        new_password_hash: New hashed password
        
    Returns:
        True if password updated successfully, False otherwise
    """
    db = SessionLocal()
    try:
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False
        ).first()
        
        if not reset_token or is_token_expired(reset_token.expires_at):
            return False
        
        # Update user password
        user = reset_token.user
        user.password_hash = new_password_hash
        user.failed_login_attempts = 0
        user.account_locked_until = None
        
        # Mark token as used
        reset_token.used = True
        reset_token.used_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"Password reset for user {user.id}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to use password reset token: {str(e)}")
        raise SQLAlchemyError(f"Failed to use password reset token: {str(e)}")
    finally:
        db.close()


# ============================================================================
# PHASE 2: ACTIVITY LOG OPERATIONS
# ============================================================================

def create_activity_log(
    user_id: int,
    action: str,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[ActivityLog]:
    """
    Create a user activity log entry.
    
    PHASE 2: New feature for user activity tracking.
    
    Args:
        user_id: User ID
        action: Action type (login, logout, password_change, etc.)
        description: Optional description
        ip_address: Optional IP address
        user_agent: Optional user agent
        
    Returns:
        Created ActivityLog or None
    """
    db = SessionLocal()
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        logger.info(f"Activity log created: {action} for user {user_id}")
        return activity
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create activity log: {str(e)}")
        raise SQLAlchemyError(f"Failed to create activity log: {str(e)}")
    finally:
        db.close()


def get_user_activity_logs(user_id: int, limit: int = 50) -> List[ActivityLog]:
    """
    Get activity logs for a user.
    
    PHASE 2: New feature for user activity tracking.
    
    Args:
        user_id: User ID
        limit: Maximum number of logs to return (default: 50)
        
    Returns:
        List of ActivityLog objects
    """
    db = SessionLocal()
    try:
        logs = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
        return logs
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve activity logs: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve activity logs: {str(e)}")
    finally:
        db.close()


# ============================================================================
# PHASE 2: AUDIT LOG OPERATIONS
# ============================================================================

def create_audit_log(
    org_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    user_id: Optional[int] = None,
    changes: Optional[Dict] = None,
    description: Optional[str] = None
) -> Optional[AuditLog]:
    """
    Create an organization audit log entry.
    
    PHASE 2: New feature for organization audit tracking.
    
    Args:
        org_id: Organization ID
        action: Action type (member_added, role_changed, etc.)
        resource_type: Type of resource affected (user, workstation, etc.)
        resource_id: ID of affected resource
        user_id: User who performed the action
        changes: Changes made (old -> new)
        description: Optional description
        
    Returns:
        Created AuditLog or None
    """
    db = SessionLocal()
    try:
        audit = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            description=description
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        logger.info(f"Audit log created: {action} in organization {org_id}")
        return audit
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create audit log: {str(e)}")
        raise SQLAlchemyError(f"Failed to create audit log: {str(e)}")
    finally:
        db.close()


def get_org_audit_logs(org_id: int, limit: int = 100) -> List[AuditLog]:
    """
    Get audit logs for an organization.
    
    PHASE 2: New feature for organization audit tracking.
    
    Args:
        org_id: Organization ID
        limit: Maximum number of logs to return (default: 100)
        
    Returns:
        List of AuditLog objects
    """
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).filter(
            AuditLog.org_id == org_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve audit logs: {str(e)}")
        raise SQLAlchemyError(f"Failed to retrieve audit logs: {str(e)}")
    finally:
        db.close()


def get_organization_member_count(org_id: int) -> int:
    """
    Get member count for an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Number of members in the organization
    """
    db = SessionLocal()
    try:
        count = db.query(UserOrganization).filter(
            UserOrganization.org_id == org_id
        ).count()
        return count
    except SQLAlchemyError as e:
        logger.error(f"Failed to get member count: {str(e)}")
        return 0
    finally:
        db.close()