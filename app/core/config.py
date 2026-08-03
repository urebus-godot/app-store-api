from typing import Optional
from datetime import timedelta
from pathlib import Path
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

    TEST: bool = False

    DB_URL: str
    TEST_DB_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
        )

    REDIS_URL: str

    BROKER_URL: str
    RESULT_BACKEND_URL: str
    BASE_TASK_PATH: str = "app.task_queue.tasks"
    CELERY_TASKS_PATH: list[str] = [
        f"{BASE_TASK_PATH}.db_tasks", 
        f"{BASE_TASK_PATH}.image_tasks"
        ]
    WORKER_DB_URL: str
    TEST_WORKER_DB_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/test_db"
        )

    WINDOW_SECONDS: int = 30
    REQUEST_LIMIT: int = 120

    CACHE_TTL_SECONDS: int = 3600

    DB_OUTPUT: bool = False
    DEBUG: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(minutes=120)
    REFRESH_TOKEN_EXPIRE_DAYS: timedelta = timedelta(days=7)

    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    TEST_ACCESS_SECRET_KEY: str = (
        "4a834639b4bee7011b42f243748c17f13c7aa211a86a06843b5683376e8f35d8"
        )

    TEST_REFRESH_SECRET_KEY: str = (
        "5ab55156e7460135f49653aa4ad50f768d0771201e236cfa986542c6b48f4b2c"
        )

    JWT_ALGORITHM: str = "HS256"

    MIN_PASSWORD_LEN: int = 8

    MIN_TITLE_LEN: int = 3
    MAX_TITLE_LEN: int = 64

    MIN_NAME_LEN: int = 3
    MAX_NAME_LEN: int = 64

    LOGGING_LEVEL: int = logging.DEBUG
    LOG_FILE_PATH: Optional[str] = None#"app_logs.log"

    FILE_BASE_PATH: Path = Path("media")
    STATIC_BASE_PATH: Path = FILE_BASE_PATH / Path("static")

    APP_ARCHIVE_PATH: Path = FILE_BASE_PATH / Path("app_archives")
    APP_COVER_PATH: Path = STATIC_BASE_PATH / Path("applications/covers")
    APP_THUMBNAIL_PATH: Path = (
        STATIC_BASE_PATH / Path("applications/thumbnails")
        )

    PROFILE_PICTURE_PATH: Path = STATIC_BASE_PATH / Path("profile_pictures")

    ARCHIVE_EXTENSIONS: list[str] = [".rar", ".zip", ".7z"]
    IMAGE_EXTENSIONS: list[str] = [".PNG", ".jpg", ".jpeg", ".webp"]

    MAX_APP_ARCHIVE_SIZE_MB: int = 1024
    MAX_APP_COVER_SIZE_MB: int = 5
    MAX_PROFILE_PICTURE_SIZE_MB: int = 1

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
            <h2>Details</h2>
            <p><b>Total price: <i>%s</i></b></p>
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
            Enter it to receive %s rubles on the balance.
            <p><b>Promo code: <i>%s</i></b></p>
            <p><b>Time of issue: <i>%s</i></b></p>
            <p><b>Expiration time: <i>%s</i></b></p>
        </h3>
    </body>
"""


settings = Settings()
