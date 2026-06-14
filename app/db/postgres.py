from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings

engine = create_async_engine(
    url=settings.DB_URL
)


async def get_session():
    async with AsyncSession(bind=engine) as session:
        yield session