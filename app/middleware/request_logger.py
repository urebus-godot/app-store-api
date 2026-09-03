import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_var

logger = logging.getLogger("middleware.request")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID")
        request_id = request_id or str(uuid4())
        rid_token = request_id_var.set(request_id)

        start_time = perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (perf_counter() - start_time) * 1000
        except Exception:
            logger.exception(
                "Unhandled error occurred",
                extra={
                    "method": request.method,
                    "url": request.url
                }
            )
            raise
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response
