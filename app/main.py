from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from httpx import AsyncClient

from app.middleware.request_logger import RequestLoggerMiddleware

from app.core.exception_handlers import exception_handlers

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
    exception_handlers=exception_handlers
)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Remaining",
    ],
    allow_credentials=True
)


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
    tags=["Finance"]
)

app.include_router(
    app_archive_router.router, 
    prefix="/api/v1/app_archives/{app_id}", 
    tags=["App archives"]
)

app.include_router(
    media_router.router, 
    prefix="/api/v1/media", 
    tags=["Media"]
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
