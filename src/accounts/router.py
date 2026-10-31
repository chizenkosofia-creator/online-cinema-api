from datetime import datetime, timedelta, timezone
import secrets
from src.security.password import verify_password
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import get_db
from src.accounts.models import UserModel, ActivationToken
from src.accounts.schemas import (
    EmailRequestSchema,
    UserRegisterSchema,
    UserResponseSchema,
    UserLoginSchema,
    TokenResponseSchema
)
from src.security.token import create_access_token, create_refresh_token
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED,
    response_model=UserResponseSchema,
    summary="Register a new user",
    description="Creates a new inactive user in the system and triggers activation token generation.")
async def register_user(
    payload: UserRegisterSchema,
    db: AsyncSession = Depends(get_db)
):
    """
        - **email**: user's unique email address.
        - **password**: secure password (truncated to 72 bytes for bcrypt safety).
        - **group_id**: user group identifier (default is 1).
    """
    result = await db.execute(select(UserModel).where(UserModel.email == payload.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    new_user = UserModel(
        email=payload.email,
        password=payload.password,
        group_id=1,
        is_active=True
    )
    db.add(new_user)
    await db.commit()

    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.group)) # або інший пов'язаний атрибут, який вимагає схема
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
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
