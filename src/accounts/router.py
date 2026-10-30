from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import get_db
from src.accounts.models import UserModel, ActivationToken
from src.accounts.schemas import EmailRequestSchema

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/resend-activation", status_code=status.HTTP_200_OK)
async def resend_activation_token(
    payload: EmailRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email was not found."
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already activated."
        )

    existing_token_result = await db.execute(
        select(ActivationToken).where(ActivationToken.user_id == user.id)
    )
    existing_token = existing_token_result.scalar_one_or_none()
    if existing_token:
        await db.delete(existing_token)

    new_token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.ACTIVATION_TOKEN_HOURS)

    new_activation_token = ActivationToken(
        user_id=user.id,
        token=new_token_str,
        expires_at=expires_at
    )
    db.add(new_activation_token)
    await db.commit()

    return {"message": "A new activation link has been sent to your email."}
