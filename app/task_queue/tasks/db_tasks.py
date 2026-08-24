from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import asyncio

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, extract, select, update

from app.core.config import settings
from app.utils.time import get_time_string
from app.utils.email_send import send_email

from app.task_queue.celery_app import celery_app, redis_client, logger

from app.models.app import AppDB
from app.models.review import ReviewDB
from app.models.user import UserDB

engine = create_engine(settings.WORKER_DB_URL)

SessionLocal = sessionmaker(
    bind=engine, 
    class_=Session, 
    autoflush=False, 
    expire_on_commit=False
    )


@celery_app.task(name="tasks.update_app_rating")
def update_app_rating(app_id: str) -> None:
    with SessionLocal() as session:
        app_id = UUID(app_id)
        result = session.exec(
            select(func.count(ReviewDB.id), func.avg(ReviewDB.rating))
            .where(ReviewDB.app_id == app_id)
        ).first()
        review_count, avg_rating = result

        if review_count > 0:    
            new_rating = round(avg_rating / review_count, 1)
        else:
            new_rating = None

        session.exec(
            update(AppDB)
            .where(AppDB.id == app_id)
            .values(rating=new_rating)
        )
        session.commit()


@celery_app.task(name="tasks.check_for_users_birthday")
def check_for_users_birthday() -> list[str]:
    """
    Finds users whose birth_date attribute matches the current date,
    stores promo codes for them in Redis and sends them emails.

    Returns generated promo codes.
    """
    with SessionLocal() as session:
        now = datetime.now()
        current_date = now.date()
        stmt = (
            select(UserDB)

        )

        users: list[UserDB] = session.exec(stmt).all()
        logger.debug(f"{users = }")
        codes = []

        for user in users:
            if user.email is not None:
                redis = redis_client.redis
                balance = 500
                code = uuid4()
                codes.append(code)

                redis.set(
                    name=f"promo_codes:{code}",
                    value=balance,
                    ex=3600 * 24
                )
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
