from celery import Celery
from celery.schedules import crontab
from src.config.settings import settings

celery_app = Celery(
    "cinema_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-every-hour": {
        "task": "src.apps.auth.tasks.cleanup_expired_tokens",
        "schedule": crontab(minute=0, hour="*"),  # Every hour
    },
}
