from datetime import datetime, timedelta, timezone
import logging
from src.security.password import verify_password, get_password_hash
from src.security.token import generate_random_token
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import get_db
from src.accounts.models import UserModel, ActivationToken, PasswordResetToken, UserGroup
from src.accounts.schemas import (
    EmailRequestSchema,
    UserRegisterSchema,
    UserResponseSchema,
    TokenResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
)
from src.security.token import create_access_token, create_refresh_token
from src.email_service import send_activation_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger(__name__)

@router.post("/register", status_code=status.HTTP_201_CREATED,
             response_model=UserResponseSchema,
             summary="Register a new user",
             description="Creates a new inactive user in the system and triggers activation token generation and email delivery.")
async def register_user(
        payload: UserRegisterSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == payload.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    group_result = await db.execute(select(UserGroup).where(UserGroup.name == "USER"))
    user_group = group_result.scalar_one_or_none()
    if not user_group:
        user_group = UserGroup(name="USER")
        db.add(user_group)
        await db.flush()

    new_user = UserModel(
        email=payload.email,
        _hashed_password=get_password_hash(payload.password),
        group_id=user_group.id,
        is_active=False
    )
    db.add(new_user)
    await db.flush()

    new_token_str = generate_random_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.ACTIVATION_TOKEN_HOURS)

    new_activation_token = ActivationToken(
        user_id=new_user.id,
        token=new_token_str,
        expires_at=expires_at
    )
    db.add(new_activation_token)
    await db.commit()

    try:
        await send_activation_email(new_user.email, new_token_str)
    except Exception as e:
        logger.exception(f"Failed to send activation email to {new_user.email}: {e}")

    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.group))
        .where(UserModel.id == new_user.id)
    )
    user_with_relations = result.scalar_one()

    return user_with_relations


@router.post("/login", response_model=TokenResponseSchema)
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user._hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not activated."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not activated."
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


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
        await db.flush()

    new_token_str = generate_random_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.ACTIVATION_TOKEN_HOURS)

    new_activation_token = ActivationToken(
        user_id=user.id,
        token=new_token_str,
        expires_at=expires_at
    )
    db.add(new_activation_token)
    await db.commit()

    try:
        await send_activation_email(user.email, new_token_str)
    except Exception as e:
        logger.exception(f"Failed to send activation email to {user.email}: {e}")

    return {"message": "A new activation link has been sent to your email."}


@router.post("/activate", status_code=status.HTTP_200_OK)
async def activate_user_account(
        token: str,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ActivationToken)
        .options(selectinload(ActivationToken.user))
        .where(ActivationToken.token == token)
    )
    activation_token = result.scalar_one_or_none()

    if not activation_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired activation token."
        )

    expires_at = activation_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        await db.delete(activation_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired."
        )

    user = activation_token.user
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already activated."
        )

    user.is_active = True
    await db.delete(activation_token)
    await db.commit()

    return {"message": "Account successfully activated."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
        payload: PasswordResetRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == payload.email))
    user = result.scalar_one_or_none()

    if user:
        old_token_result = await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        old_token = old_token_result.scalar_one_or_none()
        if old_token:
            await db.delete(old_token)
            await db.flush()

        reset_token_str = generate_random_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Наприклад, 1 година на скидання

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token_str,
            expires_at=expires_at
        )
        db.add(reset_token)
        await db.commit()

        try:
            await send_password_reset_email(user.email, reset_token_str)
        except Exception:
            pass

    return {"message": "If the email exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
        payload: PasswordResetConfirmSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token == payload.token)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired."
        )

    user = reset_token.user
    user._hashed_password = get_password_hash(payload.new_password)

    await db.delete(reset_token)
    await db.commit()

    return {"message": "Password has been successfully reset."}
