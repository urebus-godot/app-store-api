from prometheus_client import Counter, Histogram

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks.",
    labelnames=("task_name", "status")
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time",
    labelnames=("task_name",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

celery_task_retries_total = Counter(
    "celery_task_retries_total",
    "Total number of celery task retries."
)