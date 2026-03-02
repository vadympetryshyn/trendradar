from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import settings


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username or "",
        MAIL_PASSWORD=settings.mail_password or "",
        MAIL_FROM=settings.mail_from or settings.mail_username or "noreply@example.com",
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=settings.mail_use_credentials,
        VALIDATE_CERTS=True,
    )


async def send_verification_email(email: str, token: str) -> None:
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"

    html_content = f"""
    <html>
    <body>
        <h2>Welcome to TrendRadar!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_link}">Verify Email</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p>{verification_link}</p>
        <p>If you didn't create an account, you can safely ignore this email.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Verify your TrendRadar email",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )

    conf = _get_mail_config()
    fm = FastMail(conf)

    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Failed to send verification email to {email}: {e}")


async def send_password_reset_email(email: str, token: str) -> None:
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"

    html_content = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password for your TrendRadar account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p>{reset_link}</p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request a password reset, you can safely ignore this email.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Reset your TrendRadar password",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )

    conf = _get_mail_config()
    fm = FastMail(conf)

    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {e}")
