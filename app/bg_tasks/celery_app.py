from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL
)

celery_app.autodiscover_tasks(
    [settings.CELERY_TASKS_PATH]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check_for_users_birthday_everyday": {
        "task": "celery_tasks.check_for_users_birthday",
        "schedule": crontab(hour=12, minute=0)
    }
}
