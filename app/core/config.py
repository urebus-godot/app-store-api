from os import environ
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_TITLE: str = "Games Store API"
    API_DESC: str = "REST API of the videogame store"

    DB_URL: str = environ.get("DB_URL")

settings = Settings()