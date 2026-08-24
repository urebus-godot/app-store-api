from typing import Optional
import logging

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

    DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/db"
    TEST_DB_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
        )

    REDIS_URL: str = "redis://redis:6379/0"

    BROKER_URL: str = "redis://redis:6379/0"
    RESULT_BACKEND_URL: str = "redis://redis:6379/0"
    WORKER_DB_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/db"
    TEST_WORKER_DB_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/test_db"
        )

    WINDOW_SECONDS: int = 5
    REQUEST_LIMIT: int = 10

    CACHE_TTL_SECONDS: int = 3600

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ADMIN_PASSWORD: str = "secret"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ACCESS_SECRET_KEY: str = "secret"
    REFRESH_SECRET_KEY: str = "secret"

    TEST_ACCESS_SECRET_KEY: str = (
        "4a834639b4bee7011b42f243748c17f13c7aa211a86a06843b5683376e8f35d8"
        )
    TEST_REFRESH_SECRET_KEY: str = (
        "5ab55156e7460135f49653aa4ad50f768d0771201e236cfa986542c6b48f4b2c"
        )

    JWT_ALGORITHM: str = "HS256"

    AUTH_TIMEOUT: float = 5.0

    MIN_PASSWORD_LEN: int = 8

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 64

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 64

    LOGGING_LEVEL: int = logging.DEBUG
    LOG_FILE_PATH: Optional[str] = None#"app_logs.log"

    MINIO_ACCESS_KEY: str = "secret"
    MINIO_SECRET_KEY: str = "secret"
    MINIO_INTERNAL_ENDPOINT: str = "http://minio:9000"
    MINIO_PUBLIC_ENDPOINT: str = "http://localhost:9000"

    APP_ARCHIVE_BUCKET: str = "app-archives"
    APP_COVER_BUCKET: str = "app-covers"
    APP_ICON_BUCKET: str = "app-icons"
    USER_AVATAR_BUCKET: str = "user-avatars"

    THUMBNAIL_SIZE: tuple[int, int] = (128, 128)
    MEDIUM_SIZE: tuple[int, int] = (640, 640)
    IMAGE_SIZES: tuple[tuple, tuple] = ((THUMBNAIL_SIZE, "thumb"), (MEDIUM_SIZE, "medium"))

    UPLOAD_TTL_SECONDS: int = 600
    DOWNLOAD_TTL_SECONDS: int = 300

    MAX_AVATAR_ICON_SIZE_MB: int = 5
    MAX_COVER_SIZE_MB: int = 10

    MAIL_USERNAME: str = "satalovserge"
    MAIL_PASSWORD: str = "secret"
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
            <h2>Details</h2>
            <p><b>Total price: <i>%s rubles</i></b></p>
            <p><b>Applications: <i>%s</i></b></p>
            <p><b>Time of purchase: <i>%s</i></b></p>
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
            <p><b>Time of login: <i>%s</i></b></p>
        </h3>
    </body>
    """

    BIRTHDAY_CODE_TEMPLATE: str = """
    <body>
        <h3>
            Happy birthday, %s! You receive a promo code as a gift. 
            Enter it to top up your balance.
            <p><b>Promo code: <i>%s</i></b></p>
            <p><b>Amount: <i>%s</i></b></p>
            <p><b>Time of issue: <i>%s</i></b></p>
            <p><b>Expiration time: <i>%s</i></b></p>
        </h3>
    </body>
    """


settings = Settings()
