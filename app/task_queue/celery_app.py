from celery import Celery
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from app.core.config import settings

BASE_TASK_PATH = "app.task_queue.tasks"

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL
)

celery_app.autodiscover_tasks(
    [
        f"{BASE_TASK_PATH}.db_tasks", 
        f"{BASE_TASK_PATH}.image_tasks"
    ]
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
        "task": "tasks.check_for_users_birthday",
        "schedule": crontab(hour=12, minute=0)
    }
}

logger = get_task_logger(__name__)