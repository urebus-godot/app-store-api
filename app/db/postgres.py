from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine = create_async_engine(
    url=settings.DB_URL,
    echo=settings.DB_OUTPUT
)


async def get_session():
    async with AsyncSession(bind=engine, expire_on_commit=False) as session:
        yield session