from pathlib import Path
from typing import Optional
import asyncio

from PIL import Image

from app.core.logging import logger
from app.core.config import settings

from app.db.postgres import session_factory
from app.bg_tasks.celery_app import celery_app
from app.bg_tasks.bg_tasks import send_email

from app.repo.user_repo import UserRepository


@celery_app.task(name="celery_tasks.process_image")
def process_image(
    path: str, 
    size: Optional[tuple[int, int]] = None,
    quality: int = 75
    ):
    path = Path(path)
    with Image.open(path) as img:
        logger.info(f"\n\n{path}\n\n")
        img = img.convert("RGB")
        if size is not None:
            img.thumbnail(size)
        img.save(path, quality=quality)
        logger.info(f"Saved image.\nSize: {img.size}\nMode: {img.mode}")


@celery_app.task(name="celery_tasks.check_for_users_birthday")
def check_for_users_birthday():
    async def coro():
        async with session_factory() as session:
            user_repo = UserRepository(session)
            users = await user_repo.get_users_with_birthday()

            for user in users:
                if user.email is not None:
                    send_email(
                        recipients=[user.email],
                        subject="Happy birthday!",
                        body=settings.BIRTHDAY_CODE_TEMPLATE
                    )
                
    asyncio.run(coro())
