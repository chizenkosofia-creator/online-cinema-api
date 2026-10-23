import asyncio
from datetime import datetime, timezone
from sqlalchemy import delete

from src.accounts.models import ActivationToken, PasswordResetToken, RefreshToken
from src.celery_app import celery_app
from src.database import AsyncSessionLocal


async def _async_cleanup_expired_tokens():
    """Delete all expired activation, password reset, and refresh tokens."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                delete(ActivationToken).where(ActivationToken.expires_at < now)
            )
            await session.execute(
                delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
            )
            await session.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < now)
            )


@celery_app.task
def cleanup_expired_tokens():
    asyncio.run(_async_cleanup_expired_tokens())
