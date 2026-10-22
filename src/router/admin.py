from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts import User, UserGroup, UserGroupEnum
from app.schemas.accounts import UserResponseSchema
from app.database import get_current_admin_user, get_db

admin_router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])


@admin_router.patch("/{user_id}/activate", response_model=UserResponseSchema)
async def manually_activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Manually activate a user account (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


@admin_router.patch("/{user_id}/group", response_model=UserResponseSchema)
async def change_user_group(
    user_id: int,
    new_group: UserGroupEnum,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Change user group / role (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    group_result = await db.execute(select(UserGroup).where(UserGroup.name == new_group))
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group specified",
        )

    user.group_id = group.id
    await db.commit()
    await db.refresh(user)
    return user
