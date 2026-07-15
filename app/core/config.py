import logging
from typing import Optional
from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
        )

    API_TITLE: str = "App Store API"
    API_DESC: str = (
        "REST API of an online store for desktop applications and video games"
    )
    API_VERSION: str = "1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DB_URL: str
    TEST_DB_URL: str

    REDIS_URL: str

    WINDOW_SECONDS: int = 30
    REQUEST_LIMIT: int = 20

    CACHE_TTL_SECONDS: int = 3600

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(minutes=120)
    REFRESH_TOKEN_EXPIRE_DAYS: timedelta = timedelta(days=7)

    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    TEST_SECRET_KEY: str = (
        "4a834639b4bee7011b42f243748c17f13c7aa211a86a06843b5683376e8f35d8"
        )

    JWT_ALGORITHM: str = "HS256"

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 40

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 30

    MAX_DESC_LEN: int = 400

    LOGGING_LEVEL: int = logging.INFO
    LOG_FILE_PATH: Optional[str] = None

    MAIL_USERNAME: str = "satalovserge"
    MAIL_PASSWORD: str
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


settings = Settings()
