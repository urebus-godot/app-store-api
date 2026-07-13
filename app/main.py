from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging, logger
from app.api.v1 import (
    app_router,
    purchase_router,
    review_router,
    user_router,
    discussion_router,
    finance_router
)
from app.core.config import settings
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
    description=settings.API_DESC_FULL,
    debug=settings.DEBUG,
    version=settings.API_VERSION,
    lifespan=lifespan,
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

cors = CORSMiddleware(
    app=app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_credentials=True,
)


@app.get("/health", tags=["Server"])
async def health_check() -> dict[str, str]:
    return {"status": "Healthy"}


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
