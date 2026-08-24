from celery import Celery
from celery.schedules import crontab
from celery.signals import (
    setup_logging as setup_logging_signal, 
    worker_shutdown as worker_shutdown_signal
)
import logging

from app.db.redis import connect_to_sync_redis_client

from app.core.config import settings
from app.core.logging import setup_logging

BASE_TASK_PATH = "app.task_queue.tasks"

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL
)

redis_client = connect_to_sync_redis_client()


@setup_logging_signal.connect
def configure_celery_logging(*args, **kwargs):
    setup_logging()

@worker_shutdown_signal.connect
def on_worker_shutdown(*args, **kwargs):
    redis_client.close_conn()


celery_app.autodiscover_tasks(
    [
        f"{BASE_TASK_PATH}.db_tasks", 
        f"{BASE_TASK_PATH}.media_tasks"
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

logger = logging.getLogger("app.task_queue.celery_app")