from decimal import Decimal
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from src.config.settings import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_payment_confirmation_email(
    email: EmailStr, order_id: int, amount: Decimal
) -> None:
    """Send an email confirmation to the user upon successful payment."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Payment Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2b6cb0;">Payment Successful!</h2>
                <p>Hello,</p>
                <p>Your payment of <strong>${amount}</strong> for Order <strong>#{order_id}</strong> has been successfully processed.</p>
                <p>Thank you for choosing our Online Cinema service. You can now enjoy your movies!</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #777;">If you have any questions, feel free to contact our support team.</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=f"Payment Successful - Order #{order_id}",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_activation_email(email: EmailStr, token: str) -> None:
    activation_link = f"http://localhost:8000/api/v1/auth/activate?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head><meta charset="UTF-8"><title>Account Activation</title></head>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2b6cb0;">Welcome to Online Cinema!</h2>
                <p>Please activate your account by clicking the link below:</p>
                <p><a href="{activation_link}" style="background-color: #2b6cb0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Activate Account</a></p>
                <p>Or use this token directly: <code>{token}</code></p>
            </div>
        </body>
    </html>
    """
    message = MessageSchema(
        subject="Account Activation - Online Cinema",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: EmailStr, token: str) -> None:
    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head><meta charset="UTF-8"><title>Password Reset</title></head>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #e53e3e;">Password Reset Request</h2>
                <p>You requested a password reset. Click the link below to set a new password:</p>
                <p><a href="{reset_link}" style="background-color: #e53e3e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p><small>If you didn't request this, please ignore this email.</small></p>
            </div>
        </body>
    </html>
    """
    message = MessageSchema(
        subject="Password Reset - Online Cinema",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
