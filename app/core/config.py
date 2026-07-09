import logging
from os import environ
from typing import Optional
from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_TITLE: str = "App Store API"
    API_DESC: str = "REST API of an online store for desktop applications and video games"
    API_DESC_FULL: str = API_DESC
    API_VERSION: str = "1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DB_URL: str = environ.get("DB_URL")
    TEST_DB_URL: str = "sqlite+aiosqlite:///:memory:"

    REDIS_URL: str  = environ.get("REDIS_URL")
    TEST_REDIS_URL: str = environ.get("TEST_REDIS_URL")

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(minutes=15)
    REFRESH_TOKEN_EXPIRE_DAYS: timedelta = timedelta(days=7)

    SECRET_KEY: str = environ.get("SECRET_KEY")
    TEST_SECRET_KEY: str = environ.get("TEST_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 40

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 30

    MAX_DESC_LEN: int = 400

    LOGGING_LEVEL: int = logging.INFO
    LOG_FILE_PATH: Optional[str] = None#"C:/Users/user/Desktop/app_store_api.log"

    MAIL_USERNAME = "satalovserge"
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_FROM = "satalovserge@gmail.com"
    MAIL_PORT = 587
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_FROM_NAME="satalovserge"
    MAIL_STARTTLS = True
    MAIL_SSL_TLS = False
    USE_CREDENTIALS = True
    VALIDATE_CERTS = True
    
load_dotenv()

settings = Settings()