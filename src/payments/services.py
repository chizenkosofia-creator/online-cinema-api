import stripe
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


from src.config import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_stripe_checkout_session(order, success_url: str, cancel_url: str) -> tuple[str, str]:
    """Create a Stripe Checkout Session for an order and return (checkout_url, session_id)."""
    line_items = []

    for item in order.items:
        unit_amount = int(item.price_at_order * 100)
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Movie Item #{item.movie_id}",
                },
                "unit_amount": unit_amount,
            },
            "quantity": 1,
        })

    # Приклад виклику Stripe API (розкоментуйте, коли налаштуєте ключ)
    # session = stripe.checkout.Session.create(
    #     payment_method_types=["card"],
    #     line_items=line_items,
    #     mode="payment",
    #     success_url=success_url,
    #     cancel_url=cancel_url,
    #     metadata={
    #         "order_id": str(order.id),
    #         "user_id": str(order.user_id),
    #     }
    # )
    # return session.url, session.id

    # Mock-повернення для розробки до налаштування ключа Stripe:
    return f"https://checkout.stripe.com/pay/mock_session_{order.id}", f"cs_test_mock_{order.id}"