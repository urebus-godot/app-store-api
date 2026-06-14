from app.core.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.API_TITLE,
    summary=settings.API_DESC
)


app.add_route