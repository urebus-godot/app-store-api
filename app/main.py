from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError

from sqlalchemy import text

import botocore.exceptions as boto_exceptions

import httpx
from httpx import AsyncClient

from app.middleware.request_logger import RequestLoggerMiddleware
from app.core.exception_handlers import (
    response_validation_error_handler,
    request_error_handler,
    timeout_error_handler,
    boto_client_error_handler
)
from app.core.logging import setup_logging
from app.core.config import settings

from app.api.dependencies import RedisDep, SessionDep, get_object_storage
from app.api.v1 import (
    app_archive_router,
    app_router,
    media_router,
    purchase_router,
    review_router,
    user_router,
    discussion_router,
    finance_router
)
from app.db.redis import connect_to_redis_client

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_client = connect_to_redis_client()
    app.state.conversion_api_client = AsyncClient(
        base_url="https://api.frankfurter.dev/v2"
    )
    object_storage = get_object_storage()

    for bucket_name, public in settings.BUCKETS.items():
        await object_storage.create_bucket(bucket_name, public)

    yield
    
    await app.state.redis_client.close_conn()
    await app.state.conversion_api_client.aclose()

app = FastAPI(
    title=settings.API_TITLE,
    summary=settings.API_DESC,
    debug=settings.DEBUG,
    version=settings.API_VERSION,
    lifespan=lifespan,
    exception_handlers={
        ResponseValidationError: response_validation_error_handler,
        httpx.RequestError: request_error_handler,
        httpx.ReadTimeout: timeout_error_handler,
        boto_exceptions.ClientError: boto_client_error_handler
    }
)

app.add_middleware(RequestLoggerMiddleware)

app.include_router(
    user_router.router, 
    prefix="/api/v1", 
    tags=["User"]
)

app.include_router(
    app_router.router, 
    prefix="/api/v1", 
    tags=["Application"]
)

app.include_router(
    review_router.router, 
    prefix="/api/v1", 
    tags=["Review"]
)

app.include_router(
    purchase_router.router, 
    prefix="/api/v1", 
    tags=["Purchase"]
)

app.include_router(
    discussion_router.router, 
    prefix="/api/v1", 
    tags=["Discussion"]
)

app.include_router(
    finance_router.router, 
    prefix="/api/v1",
    tags=["Finance"]
)

app.include_router(
    app_archive_router.router, 
    prefix="/api/v1/files/apps/{app_id}", 
    tags=["App archives"]
)

app.include_router(
    media_router.router, 
    prefix="/api/v1/media", 
    tags=["Media"]
)

cors = CORSMiddleware(
    app=app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["X-RateLimit-Remaining"]
)


@app.get("/health", tags=["Server"])
async def health_check(
    redis: RedisDep,
    session: SessionDep
) -> dict[str, str]:
    unhealthy_response = JSONResponse(
        {"status": "Unhealthy"},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )
    try:
        redis_response = await redis.ping()
        db_response = await session.exec(text("SELECT 1"))

        if not redis_response or not db_response:
            return unhealthy_response
        
        return {"status": "Healthy"}
    except Exception:
        return unhealthy_response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
