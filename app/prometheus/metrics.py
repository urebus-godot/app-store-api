from prometheus_client import Counter, Histogram

# ------ Celery ------

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks",
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


# ------ Redis ------

redis_operation_duration_seconds = Histogram(
    "redis_operation_duration_seconds",
    "Execution time of an operation in Redis",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
) 

redis_cache_hits_total = Counter(
    "redis_cache_hits_total",
    "Total number of cache hits in Redis",
    labelnames=("endpoint",)
)

redis_cache_misses_total = Counter(
    "redis_cache_misses_total",
    "Total number of cache hits in Redis",
    labelnames=("endpoint",)
)

redis_rate_limiter_rejections_total = Counter(
    "redis_rate_limiter_rejections_total",
    "Total number of requests rejected by Redis rate limiter",
    labelnames=("endpoint", "method", "scope")
) 