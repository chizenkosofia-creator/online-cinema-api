from datetime import datetime
import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_current_active_user, get_current_admin_user
from src.config.settings import settings
from src.database import get_db
from src.payments.models import Payment, PaymentStatus
from src.accounts.models import UserModel
from src.payments.schemas import CheckoutSessionCreate, CheckoutSessionResponse, PaymentResponse
from src.payments.services import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    payment_data: CheckoutSessionCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint to create a Stripe checkout session for an order."""
    url, session_id = await PaymentService.create_checkout_session(db, payment_data.order_id, current_user.id)
    return CheckoutSessionResponse(checkout_url=url, session_id=session_id)


@router.get("/history", response_model=list[PaymentResponse])
async def get_user_payment_history(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint to retrieve payment history for the authenticated user."""
    return await PaymentService.get_user_history(db, current_user.id)


@router.get("/admin/all", response_model=list[PaymentResponse])
async def get_all_payments(
    user_id: int | None = Query(None),
    status_filter: PaymentStatus | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_admin: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to view all payments with optional filters."""
    query = select(Payment).options(selectinload(Payment.items))
    conditions = []
    if user_id is not None:
        conditions.append(Payment.user_id == user_id)
    if status_filter is not None:
        conditions.append(Payment.status == status_filter)
    if date_from is not None:
        conditions.append(Payment.created_at >= date_from)
    if date_to is not None:
        conditions.append(Payment.created_at <= date_to)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None),
):
    """Webhook endpoint to receive events from Stripe."""
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await PaymentService.process_successful_payment(db, session)

    return {"status": "success"}
