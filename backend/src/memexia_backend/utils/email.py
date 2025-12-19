import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from memexia_backend.config import settings
from memexia_backend.logger import logger


def send_verification_email(email: str, token: str):
    """
    Send verification email to the user.
    """
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    if not settings.ENABLE_EMAIL_VERIFICATION:
        logger.info(f"Email verification disabled. Verification link would be: {verification_link}")
        return

    subject = "Verify your email - Memexia"
    html_content = f"""
    <html>
        <body>
            <h1>Verify your email</h1>
            <p>Please click the link below to verify your email address:</p>
            <a href="{verification_link}">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_link}</p>
        </body>
    </html>
    """
    
    _send_email(email, subject, html_content)

def send_password_reset_email(email: str, token: str):
    """
    Send password reset email to the user.
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    if not settings.ENABLE_EMAIL_VERIFICATION: # Re-use this flag or add a new one for email service availability
        logger.info(f"Email service disabled. Reset link would be: {reset_link}")
        return

    subject = "Reset your password - Memexia"
    html_content = f"""
    <html>
        <body>
            <h1>Reset your password</h1>
            <p>Please click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_link}</p>
            <p>If you did not request a password reset, please ignore this email.</p>
        </body>
    </html>
    """
    
    _send_email(email, subject, html_content)

def _send_email(to_email: str, subject: str, html_content: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email

        part = MIMEText(html_content, "html")
        message.attach(part)

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, message.as_string())
            
        logger.info(f"Email sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")

