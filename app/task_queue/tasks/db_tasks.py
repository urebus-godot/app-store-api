from datetime import datetime, timedelta
from uuid import uuid4
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, select, extract

from app.core.config import settings
from app.utils.time import get_time_string
from app.utils.email_send import send_email

from app.task_queue.celery_app import celery_app, redis_client

from app.models.user import UserDB

engine = create_engine(settings.WORKER_DB_URL)

SessionLocal = sessionmaker(
    bind=engine, 
    class_=Session, 
    autoflush=False, 
    expire_on_commit=False
)


@celery_app.task(name="db_tasks.send_promo_codes_to_users")
def send_promo_codes_to_users() -> list[str]:
    """
    Находит пользователей, чьи *birth_date* равны текущей дате,
    создаёт промокоды в Redis и отправляет им email.

    **Возвращает**: список сгенерированных кодов."""
    with SessionLocal() as session:
        now = datetime.now()
        current_date = now.date()
        stmt = (
            select(UserDB)
            .where(
                extract("month", UserDB.birth_date) == current_date.month,
                extract("day", UserDB.birth_date) == current_date.day,
            )
        )
        users: list[UserDB] = session.exec(stmt).all()
        codes = []

        for user in users:
            redis = redis_client.redis
            balance = 500
            code = uuid4().hex
            codes.append(code)

            redis.set(
                name=f"promo_codes:{code}",
                value=balance,
                ex=3600 * 24
            )
            if user.email is not None:
                tomorrow_time = get_time_string(
                    now + timedelta(days=1)
                )
                email_body = settings.BIRTHDAY_CODE_TEMPLATE % (
                    user.username,
                    code, 
                    balance,
                    get_time_string(),
                    tomorrow_time
                )
                asyncio.run(
                    send_email(
                        [str(user.email)], 
                        "Happy birthday!", 
                        email_body
                    )
                )

    return codes
