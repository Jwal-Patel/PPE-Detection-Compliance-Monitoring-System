"""
Security utilities for password hashing, verification, and token generation.
Uses bcrypt for secure password management.
PHASE 2: Enhanced security with token generation and password reset.
"""

import bcrypt
import re
import secrets
import string
from typing import Tuple
from datetime import datetime, timedelta


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plain-text password to hash
        
    Returns:
        Hashed password string (bcrypt hash)
        
    Raises:
        ValueError: If password is empty or invalid
    """
    if not password or len(password.strip()) == 0:
        raise ValueError("Password cannot be empty")
    
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.
    
    Args:
        password: Plain-text password to verify
        password_hash: Bcrypt hash to check against
        
    Returns:
        True if password matches hash, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except (ValueError, AttributeError):
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength against security requirements.
    
    Requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character (!@#$%^&*)
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Password must contain at least 1 uppercase letter"
    
    if not has_lower:
        return False, "Password must contain at least 1 lowercase letter"
    
    if not has_digit:
        return False, "Password must contain at least 1 digit"
    
    if not has_special:
        return False, "Password must contain at least 1 special character (!@#$%^&*)"
    
    return True, "Password is strong"


def validate_email_format(email: str) -> Tuple[bool, str]:
    """
    Validate email format using regex pattern.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not email or len(email.strip()) == 0:
        return False, "Email cannot be empty"
    
    if len(email) > 255:
        return False, "Email is too long (max 255 characters)"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, "Email format is valid"


# PHASE 2: New security functions

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in characters
        
    Returns:
        Secure random token (hexadecimal)
    """
    return secrets.token_hex(length // 2)


def generate_verification_token() -> str:
    """
    Generate an email verification token.
    
    Returns:
        Secure random token for email verification
    """
    return generate_secure_token(32)


def generate_password_reset_token() -> str:
    """
    Generate a password reset token.
    
    Returns:
        Secure random token for password reset
    """
    return generate_secure_token(32)


def get_token_expiry(hours: int = 24) -> datetime:
    """
    Get expiry time for a token.
    
    Args:
        hours: Hours until expiry (default: 24)
        
    Returns:
        Datetime when token expires
    """
    return datetime.utcnow() + timedelta(hours=hours)


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check if a token has expired.
    
    Args:
        expires_at: Expiry datetime
        
    Returns:
        True if token has expired, False otherwise
    """
    return datetime.utcnow() > expires_at