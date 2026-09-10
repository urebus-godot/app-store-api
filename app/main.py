from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError


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

from app.api.deps import get_object_storage
from app.api.v1 import (
    app_archive_router,
    app_router,
    media_router,
    purchase_router,
    review_router,
    user_router,
    discussion_router,
    finance_router,
    server_router
)
from app.db.redis import connect_to_redis_client


setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_client = connect_to_redis_client()
    app.state.finance_api_client = AsyncClient(
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
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
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
    server_router.router
)

app.include_router(
    user_router.router, 
    prefix="/api/v1"
)

app.include_router(
    app_router.router, 
    prefix="/api/v1", 
    tags=["Applications"]
)

app.include_router(
    review_router.router, 
    prefix="/api/v1", 
    tags=["Reviews"]
)

app.include_router(
    purchase_router.router, 
    prefix="/api/v1"
)

app.include_router(
    discussion_router.router, 
    prefix="/api/v1", 
    tags=["Discussions"]
)

app.include_router(
    finance_router.router, 
    prefix="/api/v1",
    tags=["Finances"]
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
    allow_origins=["https://frontend.ru"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


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
