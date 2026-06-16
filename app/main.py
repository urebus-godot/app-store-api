from fastapi import FastAPI
import uvicorn
from app.core.config import settings
from app.routing import app_router, review_router, user_router

app = FastAPI(
    title=settings.API_TITLE,
    summary=settings.API_DESC
)

app.include_router(app_router.router, prefix="/api/v1")
app.include_router(review_router.router, prefix="/api/v1")
app.include_router(user_router.router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", reload=True)