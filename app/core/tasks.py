from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from PIL import Image

from pathlib import Path

from app.core.config import settings
from app.core.celery_app import celery_app

conn_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)


async def send_email(
    recipients: list[str], subject: str, body: str, subtype: str = "html"
):
    mail = FastMail(conn_config)
    message = MessageSchema(
        recipients=recipients,
        subject=str(subject),
        body=str(body),
        subtype=subtype
    )
    await mail.send_message(message)


@celery_app.task
def compress_and_save_image(path: Path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail(128, 128)
        img.save(path, quality=80)


@celery_app.task
def calculate_apps_rating():
    pass