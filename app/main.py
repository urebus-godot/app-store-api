from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError

from sqlalchemy import text

import httpx

from app.middleware.log_request import log_request
from app.core.exception_handlers import (
    response_validation_error_handler,
    file_not_found_error_handler,
    request_error_handler,
    timeout_error_handler
    )
from app.core.logging import setup_logging
from app.core.config import settings

from app.api.dependencies import RedisDep, SessionDep, rate_limit
from app.api.v1 import (
    app_router,
    purchase_router,
    review_router,
    user_router,
    discussion_router,
    finance_router,
    app_file_router,
    user_file_router
)
from app.db.redis import connect_to_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.redis_client = connect_to_redis_client()
    yield
    await app.state.redis_client.close_conn()


app = FastAPI(
    title=settings.API_TITLE,
    summary=settings.API_DESC,
    debug=settings.DEBUG,
    version=settings.API_VERSION,
    lifespan=lifespan,
    dependencies=[Depends(rate_limit)],
    exception_handlers={
        ResponseValidationError: response_validation_error_handler,
        FileNotFoundError: file_not_found_error_handler,
        httpx.RequestError: request_error_handler,
        httpx.ReadTimeout: timeout_error_handler
    }
)

app.include_router(
    user_router.router, prefix="/api/v1", tags=["User"]
    )
app.include_router(
    app_router.router, prefix="/api/v1", tags=["Application"]
    )
app.include_router(
    review_router.router, prefix="/api/v1", tags=["Review"]
    )
app.include_router(
    purchase_router.router, prefix="/api/v1", tags=["Purchase"]
    )
app.include_router(
    discussion_router.router, prefix="/api/v1", tags=["Discussion"]
    )
app.include_router(
    finance_router.router, prefix="/api/v1", tags=["Finance"]
    )
app.include_router(
    app_file_router.router, 
    prefix="/api/v1/files/apps/{app_id}", 
    tags=["Application", "Files"]
    )
app.include_router(
    user_file_router.router, prefix="/api/v1/users", tags=["User", "Files"]
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
        redis_response = await redis.ping()
        db_response = await session.exec(text("SELECT 1"))
        if not redis_response or not db_response:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Connection to redis or database failed"
            )
        return {"status": "Healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        access_log=True,
        proxy_headers=True
    )
    app.add_middleware(log_request)
