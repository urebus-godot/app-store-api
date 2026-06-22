from os import environ

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    API_TITLE: str = "App Store API"
    API_DESC: str = "REST API of an online store for desktop applications and video games"
    API_DESC_FULL: str = API_DESC

    DB_URL: str = environ.get("DB_URL")
    REDIS_URL: str  = environ.get("REDIS_URL")

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SECRET_KEY: str = environ.get("SECRET_KEY")
    ALGORITHM: str = "HS256"

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 40

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 30

    MAX_DESC_LEN: int = 400

    DUMMY_HASH: str = "dummypassword"

    REFRESH_TOKEN_KEY: str = "cache:refresh-token"
    
load_dotenv()

settings = Settings()