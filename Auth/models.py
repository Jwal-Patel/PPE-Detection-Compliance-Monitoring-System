"""
SQLAlchemy ORM models for user authentication, organizations, and workstations.
Defines the database schema for the PPE Detection Platform.
PHASE 2: Added email verification, password reset, 2FA support.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import secrets

Base = declarative_base()


class User(Base):
    """
    User model representing a platform user account.
    
    PHASE 2 ADDITIONS:
    - email_verified: Track email verification status
    - email_verified_at: Timestamp of verification
    - password_reset_token: For password reset flow
    - password_reset_expires: Token expiry
    - two_factor_enabled: 2FA status
    - two_factor_secret: TOTP secret key
    - backup_codes: JSON array of backup codes
    - last_login: Track last login time
    - last_ip: Track login IP
    - failed_login_attempts: Account security
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="Viewer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # PHASE 2: Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    email_verification_token = Column(String(255), unique=True, nullable=True, index=True)
    email_verification_expires = Column(DateTime, nullable=True)
    
    # PHASE 2: Password reset
    password_reset_token = Column(String(255), unique=True, nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # PHASE 2: Two-Factor Authentication
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # List of backup codes
    
    # PHASE 2: Session & activity tracking
    last_login = Column(DateTime, nullable=True)
    last_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organizations = relationship("Organization", back_populates="admin_user", foreign_keys="Organization.admin_user_id")
    user_organizations = relationship("UserOrganization", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name}, verified={self.email_verified})>"


class Organization(Base):
    """
    Organization model representing a company or workstation group.
    
    PHASE 2 ADDITIONS:
    - settings: JSON object for organization settings
    """
    
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, nullable=True)  # Organization-wide settings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    admin_user = relationship("User", back_populates="organizations", foreign_keys=[admin_user_id])
    user_organizations = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    workstations = relationship("Workstation", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, admin={self.admin_user_id})>"


class UserOrganization(Base):
    """
    Association model linking users to organizations with role mapping.
    Enables many-to-many relationship between users and organizations.
    """
    
    __tablename__ = "user_organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    role = Column(String(50), default="Viewer", nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_organizations")
    organization = relationship("Organization", back_populates="user_organizations")
    
    def __repr__(self) -> str:
        return f"<UserOrganization(user={self.user_id}, org={self.org_id}, role={self.role})>"


class Workstation(Base):
    """
    Workstation model representing a physical detection point (camera/site).
    """
    
    __tablename__ = "workstations"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    camera_url = Column(String(500), nullable=True)
    ppe_model_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="workstations")
    detection_logs = relationship("DetectionLog", back_populates="workstation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Workstation(id={self.id}, name={self.name}, org={self.org_id})>"


class DetectionLog(Base):
    """
    Detection log model storing PPE detection results with timestamps.
    """
    
    __tablename__ = "detection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workstation_id = Column(Integer, ForeignKey("workstations.id"), nullable=False, index=True)
    frame_timestamp = Column(DateTime, nullable=False)
    worker_count = Column(Integer, default=0, nullable=False)
    compliant_count = Column(Integer, default=0, nullable=False)
    partial_count = Column(Integer, default=0, nullable=False)
    non_compliant_count = Column(Integer, default=0, nullable=False)
    ppe_breakdown = Column(JSON, nullable=True)
    raw_detections = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    workstation = relationship("Workstation", back_populates="detection_logs")
    
    def __repr__(self) -> str:
        return f"<DetectionLog(id={self.id}, workers={self.worker_count})>"


# PHASE 2: NEW MODELS

class ActivityLog(Base):
    """
    User activity logging for compliance and security.
    
    Tracks:
    - Login/logout events
    - Password changes
    - Profile updates
    - 2FA changes
    - Permission changes
    """
    
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # login, logout, password_change, etc.
    description = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self) -> str:
        return f"<ActivityLog(user={self.user_id}, action={self.action}, at={self.created_at})>"


class AuditLog(Base):
    """
    Organization audit logging for tracking organization-level changes.
    
    Tracks:
    - Member additions/removals
    - Role changes
    - Organization settings changes
    - Workstation changes
    - Detection log exports
    """
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # member_added, role_changed, etc.
    resource_type = Column(String(50), nullable=False)  # user, workstation, organization, etc.
    resource_id = Column(Integer, nullable=True)
    changes = Column(JSON, nullable=True)  # What changed (old_value -> new_value)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(org={self.org_id}, action={self.action}, at={self.created_at})>"


class PasswordResetToken(Base):
    """
    Secure token storage for password reset functionality.
    Separate table for better security and token management.
    """
    
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<PasswordResetToken(user={self.user_id}, expires={self.expires_at})>"


class EmailVerificationToken(Base):
    """
    Email verification token storage.
    Separate table for managing email verification flow.
    """
    
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)  # Email being verified
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<EmailVerificationToken(user={self.user_id}, email={self.email})>"