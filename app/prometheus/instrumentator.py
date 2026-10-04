from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics

def create_instrumentator(app: FastAPI) -> Instrumentator:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/live", "/ready"],
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    instrumentator.add(
        metrics.latency(
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
    )
    instrumentator.add(metrics.requests())
    instrumentator.add(metrics.request_size())
    instrumentator.add(metrics.response_size())
    return instrumentator