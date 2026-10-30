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