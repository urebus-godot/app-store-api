import logging
import time

from celery import Celery
from celery.schedules import crontab
from celery.signals import (
    setup_logging, 
    worker_shutdown,
    task_retry,
    task_postrun,
    task_prerun
)

from app.prometheus.setup import setup_multiproc_dir

setup_multiproc_dir()

from app.prometheus.metrics import (
    celery_task_duration_seconds, 
    celery_task_retries_total
)

from app.db.redis import connect_to_sync_redis_client

from app.core.config import settings
from app.core.logging import setup_logging

BASE_TASK_PATH = "app.task_queue.tasks"

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL
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
)

celery_app.conf.beat_schedule = {
    "send_promo_codes_to_users_everyday": {
        "task": "db_tasks.send_promo_codes_to_users",
        "schedule": crontab(hour="12", minute="0")
    }
}

_task_start_times: dict[str, float] = {}

logger = logging.getLogger("task_queue.celery_app")


@setup_logging.connect
def configure_celery_logging(*args, **kwargs):
    setup_logging(settings.LOGGING_LEVEL)


@task_retry.connect
def on_task_retry(request, reason, *args, **kwargs):
    celery_task_retries_total.labels(task_name=request.task).inc()


@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    _task_start_times[task_id] = time.perf_counter()


@task_postrun.connect
def on_task_postrun(task_id, task, retval, state, *args, **kwargs):
    started = _task_start_times.pop(task_id, None)
    if started is not None:
        celery_task_duration_seconds.labels(
            task_name=task.name
        ).observe(time.perf_counter() - started)


@worker_shutdown.connect
def on_worker_shutdown(*args, **kwargs):
    redis_client.close_conn()
