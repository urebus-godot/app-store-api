from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.api.v1 import (
    app_router,
    review_router,
    user_router,
    cart_router,
    discussion_router,
)
from app.core.config import settings
from app.db.redis import connect_to_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(user_router.router, prefix="/api/v1", tags=["User"])
app.include_router(app_router.router, prefix="/api/v1", tags=["Application"])
app.include_router(review_router.router, prefix="/api/v1", tags=["Review"])
app.include_router(cart_router.router, prefix="/api/v1", tags=["Cart"])
app.include_router(
    discussion_router.router, prefix="/api/v1", tags=["Discussion"]
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


if __name__ == "__main__":
    import uvicorn

    setup_logging()

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        access_log=True,
    )
