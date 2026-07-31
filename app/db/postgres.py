from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine = create_async_engine(
    url=settings.DB_URL, 
    echo=settings.DB_OUTPUT
    )

session_factory = async_sessionmaker(
    bind=engine, 
    autoflush=False, 
    expire_on_commit=False,
    class_=AsyncSession
    )


async def get_session() -> AsyncGenerator[AsyncSession, None, None]:
    async with session_factory() as session:
        yield session
