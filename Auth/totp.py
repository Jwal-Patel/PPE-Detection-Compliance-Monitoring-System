"""
TOTP (Time-based One-Time Password) implementation for 2FA.
Uses pyotp library for Google Authenticator compatibility.

PHASE 2: Two-Factor Authentication support.

To install: pip install pyotp qrcode
"""

import pyotp
import qrcode
import io
import base64
from typing import Tuple, List
import secrets
import string


class TOTPManager:
    """
    Manages TOTP (Two-Factor Authentication) for user accounts.
    """
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret key.
        
        Returns:
            Base32-encoded secret key for use with authenticator apps
        """
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = "PPE Detection Platform") -> str:
        """
        Get the provisioning URI for QR code generation.
        
        Args:
            secret: TOTP secret key
            email: User's email address
            issuer: Application name
            
        Returns:
            URI for QR code generation
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)
    
    @staticmethod
    def generate_qr_code(secret: str, email: str, issuer: str = "PPE Detection Platform") -> str:
        """
        Generate QR code image as base64 string.
        
        Args:
            secret: TOTP secret key
            email: User's email
            issuer: Application name
            
        Returns:
            Base64-encoded PNG image of QR code
        """
        uri = TOTPManager.get_totp_uri(secret, email, issuer)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.
        
        Args:
            secret: TOTP secret key
            token: 6-digit code from authenticator app
            window: Allow codes from adjacent time windows (default: 1 = 30 seconds)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate format: XXXX-XXXX-XXXX (12 characters + 2 dashes)
            code = '-'.join([
                ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
                for _ in range(3)
            ])
            codes.append(code)
        return codes
    
    @staticmethod
    def use_backup_code(backup_codes: List[str], code: str) -> Tuple[bool, List[str]]:
        """
        Verify and consume a backup code.
        
        Args:
            backup_codes: List of available backup codes
            code: Backup code to verify
            
        Returns:
            Tuple of (is_valid, updated_backup_codes)
        """
        if code in backup_codes:
            # Remove the used code
            updated_codes = [c for c in backup_codes if c != code]
            return True, updated_codes
        return False, backup_codes