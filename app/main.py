from fastapi import FastAPI

from app.core.logging import setup_logging
from app.api.v1 import (
    app_router, review_router, user_router, cart_router
    )
from app.core.config import settings

setup_logging()

app = FastAPI(
    title=settings.API_TITLE,
    summary=settings.API_DESC,
    description=settings.API_DESC_FULL,
    debug=settings.DEBUG
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
    cart_router.router, prefix="/api/v1", tags=["Cart"]
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "Healthy"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
    "app.main:app", 
    host=settings.APP_HOST, 
    port=settings.APP_PORT, 
    reload=True,
    access_log=True
    )