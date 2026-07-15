from time import perf_counter

from fastapi import Request, Response

from app.core.logging import logger
from app.main import app


@app.middleware("http")
async def log_request(request: Request, call_next) -> Response:
    start_time = perf_counter()

    logger.info(f"Handle request: {request.method} {request.url}")

    response = await call_next(request)
    
    process_time = perf_counter() - start_time

    logger.info(
        f"Status Code: {response.status_code}\nTime: {process_time:.5f}s"
        )
    return response
