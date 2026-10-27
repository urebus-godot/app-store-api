import logging
import time

from celery import Celery
from celery.schedules import crontab
from celery.signals import (
    setup_logging as setup_logging_signal, 
    task_retry,
    task_postrun,
    task_prerun
)
from app.prometheus.metrics import (
    celery_task_duration_seconds, 
    celery_task_retries_total,
    celery_tasks_total
)
from app.db.redis import connect_to_sync_redis_client

from app.core.config import settings
from app.core.logging import setup_logging

BASE_TASK_PATH = "app.task_queue.tasks"

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL,
    include=[
        "app.task_queue.tasks.db_tasks",
        "app.task_queue.tasks.media_tasks"
    ]
)

redis_client = connect_to_sync_redis_client()


celery_app.autodiscover_tasks(
    [
        f"{BASE_TASK_PATH}.db_tasks", 
        f"{BASE_TASK_PATH}.media_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_default_retry_delay=1,
    task_max_retries=5,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

celery_app.conf.task_routes = {
    "app.task_queue.tasks.db_tasks.*": {"queue": "images"},
    "app.task_queue.tasks.media_tasks.*": {"queue": "default"},
}
celery_app.conf.task_default_queue = "default"

celery_app.conf.beat_schedule = {
    "send_promo_codes_to_users_everyday": {
        "task": "db_tasks.send_promo_codes_to_users",
        "schedule": crontab(hour="12", minute="0")
    },
    #"options": {"queue": "default"}
}

task_start_times: dict[str, float] = {}

logger = logging.getLogger("task_queue.celery_app")


@setup_logging_signal.connect
def configure_celery_logging(*args, **kwargs):
    setup_logging(settings.LOGGING_LEVEL)


@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    task_start_times[task_id] = time.perf_counter()
    celery_tasks_total.labels(task_name=task.name, status="started").inc()


@task_postrun.connect
def on_task_postrun(task_id, task, retval, state, *args, **kwargs):
    started = task_start_times.pop(task_id, None)
    if started is not None:
        celery_task_duration_seconds.labels(
            task_name=task.name
        ).observe(time.perf_counter() - started)

    task_status = "success" if task.status == "SUCCESS" else "failed"
    celery_tasks_total.labels(task_name=task.name, status=task_status).inc()


@task_retry.connect
def on_task_retry(request, reason, *args, **kwargs):
    celery_task_retries_total.labels(task_name=request.task).inc()
    logger.info("Retrying task...")
