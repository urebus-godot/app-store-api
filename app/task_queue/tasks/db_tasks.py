from datetime import datetime, timezone, timedelta
from uuid import UUID
import asyncio

from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from app.core.logging import logger
from app.core.config import settings
from app.utils.time import get_time_string

from app.db.postgres import session_factory
from app.db.redis import get_redis

from app.task_queue.celery_app import celery_app
from app.utils.email_send import send_email

from app.models.app import AppDB
from app.models.review import ReviewDB

from app.repo.user_repo import UserRepository
from app.service.finance_service import FinanceService, FinanceRepository

engine = create_engine(settings.WORKER_DB_URL)


SessionLocal = sessionmaker(
    bind=engine, 
    class_=Session, 
    autoflush=False, 
    expire_on_commit=False
    )


@celery_app.task(name="tasks.update_app_rating")
def update_app_rating(app_id: str) -> None:
    logger.info("Start calculating app rating...")
    with SessionLocal() as session:
        reviews = session.exec(
            select(ReviewDB)
        ).all()
        logger.info(f"Reviews: {reviews}")
        app_id = UUID(app_id)
        result = session.exec(
            select(func.count(ReviewDB.id), func.avg(ReviewDB.rating))
            .where(ReviewDB.app_id == app_id)
        ).first()
        review_count, avg_rating = result
        logger.info(f"{review_count = }; {avg_rating = }")

        if review_count > 0:    
            new_rating = round(avg_rating / review_count, 1)
        else:
            new_rating = None

        logger.info(f"{new_rating = }")

        session.exec(
            update(AppDB)
            .where(AppDB.id == app_id)
            .values(rating=new_rating)
        )
        session.commit()
        logger.info("Committed")


@celery_app.task(name="tasks.check_for_users_birthday")
def check_for_users_birthday():
    async def _check():
        async with session_factory() as session:
            user_repo = UserRepository(session)
            finance_repo = FinanceRepository(session)
            finance_service = FinanceService(finance_repo, user_repo)

            redis = get_redis()
            users = await user_repo.get_users_with_birthday()

            for user in users:
                if user.email is not None:
                    balance = 500
                    code = await finance_service.create_promo_code(
                        data={"balance": balance}, 
                        expire=3600 * 24, 
                        redis=redis
                        )
                    tomorrow_time = get_time_string(
                        datetime.now(timezone.utc) + timedelta(days=1)
                        )
                    email_body = settings.BIRTHDAY_CODE_TEMPLATE % (
                            user.username,
                            balance,
                            code, 
                            get_time_string(),
                            tomorrow_time
                        )
                    await send_email(
                        recipients=[user.email],
                        subject="Happy birthday!",
                        body=email_body
                    )
                
    asyncio.run(_check())
