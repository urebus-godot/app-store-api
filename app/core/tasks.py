from fastapi_mail import FastMail, ConnectionConfig, MessageSchema

from app.core.config import settings

config = ConnectionConfig(
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
    return
    mail = FastMail(config)
    message = MessageSchema(
        recipients=recipients,
        subject=str(subject),
        body=str(body),
        subtype=subtype,  # "html"
    )
    await mail.send_message(message)
