import logging

logger = logging.getLogger(__name__)

async def send_order_confirmation_email(user_email: str, order_uuid: str, total_amount: float) -> None:
    """Send an email confirmation to the user after successful payment."""
    logger.info(
        f"Sending email notification to {user_email}: "
        f"Order {order_uuid} successfully paid. Total amount: ${total_amount}"
    )