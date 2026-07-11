import logging
from os import environ
from typing import Optional
from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_TITLE: str = "App Store API"
    API_DESC: str = (
        "REST API of an online store for desktop applications and video games"
    )
    API_DESC_FULL: str = API_DESC
    API_VERSION: str = "1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DB_URL: str = environ.get("DB_URL")
    TEST_DB_URL: str = environ.get("TEST_DB_URL")

    REDIS_URL: str = environ.get("REDIS_URL")
    TEST_REDIS_URL: str = environ.get("TEST_REDIS_URL")

    CACHE_TTL_SECONDS: int = 3600

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(minutes=15)
    REFRESH_TOKEN_EXPIRE_DAYS: timedelta = timedelta(days=7)

    SECRET_KEY: str# = environ.get("ACCESS_SECRET_KEY")
    REFRESH_SECRET_KEY: str = environ.get("REFRESH_SECRET_KEY")
    # TEST_SECRET_KEY: str = environ.get("TEST_ACCESS_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 40

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 30

    MAX_DESC_LEN: int = 400

    LOGGING_LEVEL: int = logging.INFO
    LOG_FILE_PATH: Optional[str] = (
        None  # "C:/Users/user/Desktop/app_store_api.log"
    )

    MAIL_USERNAME: str = "satalovserge"
    MAIL_PASSWORD: str = environ.get("MAIL_PASSWORD")
    MAIL_FROM: str = "satalovserge@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "satalovserge"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    RECEIPT_TEMPLATE: str = """
    <body>
        <h3>
            Apps have been purchased
        </h3>
    </body>
    """

    LOGIN_TEMPLATE: str = """
    <body>
        <h3>
            If it wasn't you, then change the password immediately!
            <hr>
            <h2>Details</h2>
            <p><b>IP address: <i>%s</i></b></p>
        </h3>
    </body>
    """


load_dotenv()

settings = Settings()
