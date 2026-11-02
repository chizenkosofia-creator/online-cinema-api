import asyncio
from datetime import datetime, timezone
from sqlalchemy import delete
from src.celery_app import celery_app
from src.database import AsyncSessionLocal
from src.accounts.models import ActivationToken

async def _async_cleanup_tokens():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        stmt = delete(ActivationToken).where(ActivationToken.expires_at < now)
        result = await db.execute(stmt)
        await db.commit()
        print(f"Successfully cleaned up {result.rowcount} expired activation tokens.")

@celery_app.task(name="src.accounts.tasks.cleanup_expired_tokens")
def cleanup_expired_tokens():
    asyncio.run(_async_cleanup_tokens())