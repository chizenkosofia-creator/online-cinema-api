from decimal import Decimal
import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.payments.models import Payment, PaymentItem, PaymentStatus
from src.orders.models import OrderModel
from src.email_service import send_payment_confirmation_email

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    @staticmethod
    async def create_checkout_session(db: AsyncSession, order_id: int, user_id: int) -> tuple[str, str]:
        order_result = await db.execute(select(OrderModel).where(OrderModel.id == order_id))
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to pay for this order")

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"Order #{order.id}"},
                            "unit_amount": int(order.total_amount * 100),
                        },
                        "quantity": 1,
                    },
                ],
                mode="payment",
                success_url=f"{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/cancel",
                metadata={"order_id": str(order.id), "user_id": str(user_id)},
            )
            return checkout_session.url, checkout_session.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": str(e),
                    "recommendation": "Try a different payment method or verify your card details.",
                },
            )

    @staticmethod
    async def get_user_history(db: AsyncSession, user_id: int) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.items))
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def process_successful_payment(db: AsyncSession, session: dict) -> None:
        metadata = session.get("metadata") or {}
        order_id = int(metadata.get("order_id"))
        user_id = int(metadata.get("user_id"))
        external_payment_id = session.get("payment_intent")
        amount_total = Decimal(session.get("amount_total", 0)) / Decimal(100)
        customer_email = session.get("customer_details", {}).get("email")

        order_result = await db.execute(select(OrderModel).where(OrderModel.id == order_id))
        order = order_result.scalar_one_or_none()
        if order:
            order.status = "paid"

        payment = Payment(
            user_id=user_id,
            order_id=order_id,
            amount=amount_total,
            status=PaymentStatus.successful,
            external_payment_id=external_payment_id,
        )
        db.add(payment)
        await db.flush()

        if order and hasattr(order, "items"):
            for item in order.items:
                payment_item = PaymentItem(
                    payment_id=payment.id,
                    order_item_id=item.id,
                    price_at_payment=item.price,
                )
                db.add(payment_item)

        await db.commit()

        if customer_email:
            await send_payment_confirmation_email(
                email=customer_email, order_id=order_id, amount=amount_total
            )
