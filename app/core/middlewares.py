from time import perf_counter

from fastapi import Request, Response

from app.main import app
from app.core.logging import logger

@app.middleware("http")
async def log_request(request: Request, call_next) -> Response:
    start_time = perf_counter()

    print(f"Handle request: {request.method} {request.url}")
    logger.info(f"Handle request: {request.method} {request.url}")

    response = await call_next(request)
    process_time = perf_counter() - start_time

    print(
        f"Response: {response.status_code}"
        f"Time: {process_time:.5f}s"
        )
    logger.info(
        f"Response: {response.status_code}"
        f"Time: {process_time:.5f}s"
    )
    return response
