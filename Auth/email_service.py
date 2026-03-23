"""
Email service for sending verification, password reset, and notification emails.
PHASE 2: Email functionality for authentication flows.

IMPORTANT: Configure these environment variables in .env file:
- EMAIL_SENDER: Your email address
- SMTP_SERVER: SMTP server (e.g., smtp.gmail.com)
- SMTP_PORT: SMTP port (e.g., 587)
- SMTP_USERNAME: SMTP username
- SMTP_PASSWORD: SMTP password (use app-specific password for Gmail)
- EMAIL_DEV_MODE: true for console output, false for actual sending
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending various notification emails.
    Supports both development (console) and production (SMTP) modes.
    """
    
    def __init__(self):
        """Initialize email service with environment variables."""
        # Load environment variables
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        self.sender_email = os.getenv("EMAIL_SENDER", "noreply@ppe-platform.com")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Development mode: print emails to console instead of sending
        self.dev_mode = os.getenv("EMAIL_DEV_MODE", "true").lower() == "true"
        
        # Log initialization
        logger.info(f"[EMAIL SERVICE] Initialized in {'DEV' if self.dev_mode else 'PRODUCTION'} mode")
        logger.info(f"[EMAIL SERVICE] SMTP Server: {self.smtp_server}")
        logger.info(f"[EMAIL SERVICE] SMTP Port: {self.smtp_port}")
        logger.info(f"[EMAIL SERVICE] Sender: {self.sender_email}")
        
        if self.dev_mode:
            logger.warning("[EMAIL SERVICE] ⚠️ DEV MODE ENABLED - Emails will print to console")
        else:
            if not self.smtp_username or not self.smtp_password:
                logger.error("[EMAIL SERVICE] ❌ PRODUCTION mode but SMTP credentials missing!")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text: Plain text version (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if self.dev_mode:
            logger.info("\n" + "="*80)
            logger.info("[DEV MODE] EMAIL WOULD BE SENT")
            logger.info("="*80)
            logger.info(f"TO: {to_email}")
            logger.info(f"FROM: {self.sender_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info("-"*80)
            logger.info("HTML CONTENT:")
            logger.info(html_content)
            logger.info("-"*80)
            if plain_text:
                logger.info("PLAIN TEXT:")
                logger.info(plain_text)
                logger.info("-"*80)
            logger.info("="*80 + "\n")
            return True
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            if plain_text:
                part1 = MIMEText(plain_text, "plain")
                message.attach(part1)
            
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            logger.info(f"[EMAIL] Connecting to {self.smtp_server}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                logger.info(f"[EMAIL] Connected to SMTP server")
                
                if self.use_tls:
                    logger.info(f"[EMAIL] Starting TLS encryption")
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    logger.info(f"[EMAIL] Authenticating as {self.smtp_username}")
                    server.login(self.smtp_username, self.smtp_password)
                else:
                    logger.warning(f"[EMAIL] No credentials provided, sending without authentication")
                
                logger.info(f"[EMAIL] Sending message to {to_email}")
                server.send_message(message)
            
            logger.info(f"[EMAIL] ✅ Email sent successfully to {to_email}")
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[EMAIL] ❌ Authentication failed: {str(e)}")
            logger.error(f"[EMAIL] Please check SMTP_USERNAME and SMTP_PASSWORD in .env file")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[EMAIL] ❌ SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"[EMAIL] ❌ Failed to send email to {to_email}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_link: str
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            to_email: User's email
            user_name: User's name
            verification_link: Link to verify email
            
        Returns:
            True if sent successfully
        """
        subject = "Verify Your Email Address - PPE Detection Platform"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                        <h1 style="margin: 0;">🛡️ PPE Detection Platform</h1>
                    </div>
                    
                    <h2>Hello, {user_name}!</h2>
                    
                    <p>Thank you for registering with the PPE Detection Platform. To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="background: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                        <code>{verification_link}</code>
                    </p>
                    
                    <p style="color: #666; font-size: 12px;">
                        This link will expire in 24 hours.<br>
                        If you didn't create this account, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <footer style="text-align: center; color: #999; font-size: 12px;">
                        <p>PPE Detection & Compliance Platform | © 2024</p>
                    </footer>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_link: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: User's email
            user_name: User's name
            reset_link: Link to reset password
            
        Returns:
            True if sent successfully
        """
        subject = "Reset Your Password - PPE Detection Platform"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                        <h1 style="margin: 0;">🛡️ PPE Detection Platform</h1>
                    </div>
                    
                    <h2>Password Reset Request</h2>
                    
                    <p>Hi {user_name},</p>
                    
                    <p>We received a request to reset the password for your account. Click the button below to set a new password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link:</p>
                    <p style="background: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                        <code>{reset_link}</code>
                    </p>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; margin: 20px 0; color: #856404;">
                        <strong>⚠️ Security Note:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email. Your password will not change unless you click the link above.
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <footer style="text-align: center; color: #999; font-size: 12px;">
                        <p>PPE Detection & Compliance Platform | © 2024</p>
                    </footer>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_2fa_setup_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """
        Send 2FA setup confirmation email.
        
        Args:
            to_email: User's email
            user_name: User's name
            
        Returns:
            True if sent successfully
        """
        subject = "Two-Factor Authentication Enabled - PPE Detection Platform"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                        <h1 style="margin: 0;">🛡️ PPE Detection Platform</h1>
                    </div>
                    
                    <h2>Two-Factor Authentication Enabled</h2>
                    
                    <p>Hi {user_name},</p>
                    
                    <p>Your account now has two-factor authentication (2FA) enabled. This adds an extra layer of security to your account.</p>
                    
                    <div style="background: #d4edda; border: 1px solid #28a745; border-radius: 5px; padding: 15px; margin: 20px 0; color: #155724;">
                        <strong>✅ 2FA is now active</strong><br>
                        You'll need to provide a one-time code from your authenticator app when you log in.
                    </div>
                    
                    <p><strong>What you should do:</strong></p>
                    <ul>
                        <li>Save your backup codes in a safe place</li>
                        <li>These codes can be used if you lose access to your authenticator app</li>
                        <li>Keep your authenticator app secure</li>
                    </ul>
                    
                    <p style="color: #666; font-size: 12px;">
                        If you didn't enable 2FA, please log in to your account and disable it immediately.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <footer style="text-align: center; color: #999; font-size: 12px;">
                        <p>PPE Detection & Compliance Platform | © 2024</p>
                    </footer>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_security_alert_email(
        self,
        to_email: str,
        user_name: str,
        alert_message: str,
        action_needed: bool = False
    ) -> bool:
        """
        Send security alert email for suspicious activities.
        
        Args:
            to_email: User's email
            user_name: User's name
            alert_message: Description of the security event
            action_needed: Whether user action is required
            
        Returns:
            True if sent successfully
        """
        subject = "Security Alert - PPE Detection Platform"
        
        action_section = ""
        if action_needed:
            action_section = """
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 20px 0; color: #721c24;">
                <strong>⚠️ Action Required:</strong><br>
                If this wasn't you, please reset your password immediately by visiting your account settings.
            </div>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                        <h1 style="margin: 0;">🛡️ PPE Detection Platform</h1>
                    </div>
                    
                    <h2>Security Alert</h2>
                    
                    <p>Hi {user_name},</p>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; margin: 20px 0; color: #856404;">
                        <strong>🔔 Security Event Detected:</strong><br>
                        {alert_message}
                    </div>
                    
                    {action_section}
                    
                    <p style="color: #666; font-size: 12px;">
                        This is an automated security notification. If you have any concerns about your account security, please contact our support team.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <footer style="text-align: center; color: #999; font-size: 12px;">
                        <p>PPE Detection & Compliance Platform | © 2024</p>
                    </footer>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)


# Global email service instance
email_service = EmailService() 