from collections.abc import AsyncGenerator
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime, timezone
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from fakeredis.aioredis import FakeRedis
import pytest_asyncio
import jwt

from app.models.user import UserDB, UserRequest, UserRole
from app.db.postgres import get_session
from app.dependencies import (
    get_current_user, get_current_user_id, get_redis
    )
from app.service.user_service import UserService
from app.repo.user_repo import UserRepository
from app.core.config import settings
from app.main import app

test_user_data = {
    "username": "testUser", 
    "hashed_password": "testPassword", 
    "email": "ureb588@gmail.com",
    "id": UUID('3076dfdd-fba4-4b11-a415-143ca0e8d21c')
    }


def create_access_token(
    user_id: UUID,
    expires_delta: datetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    extra_claims: Optional[dict[str, str]] = None
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "type": "access",
        #"jti": str(uuid4),
        **(extra_claims or {})
    }

    return jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )


def create_refresh_token(
    user_id: UUID, 
    jti: UUID = uuid4(),
    family_id: UUID = uuid4(),
    expires_delta: datetime = settings.REFRESH_TOKEN_EXPIRE_DAYS
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": jti,
        "family_id": family_id
    }
    token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )
    return token, jti, family_id


@pytest_asyncio.fixture
async def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(settings.TEST_DB_URL)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, fake_redis: FakeRedis
    ):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app)
    async with AsyncClient(
            transport=transport, base_url="http://tests"
            ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def test_auth_client(
    db_session: AsyncSession, 
    fake_redis: FakeRedis,
    test_user: UserDB, 
    access_token: str
):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_current_user_id] = lambda: test_user.id

    transport = ASGITransport(app)
    async with AsyncClient(
            transport=transport, 
            base_url="http://tests",
            headers={"Authorization": f"Bearer {access_token}"}
            ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def real_auth_client(
    db_session: AsyncSession, 
    fake_redis: FakeRedis,
    access_token: str
):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    
    transport = ASGITransport(app)
    async with AsyncClient(
            transport=transport, 
            base_url="http://tests",
            headers={"Authorization": f"Bearer {access_token}"}
            ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin():
        async with AsyncSession(
                bind=engine, expire_on_commit=False
                ) as session:
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def fake_redis() -> AsyncGenerator[FakeRedis, None]:
    redis = FakeRedis()
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest_asyncio.fixture
def access_token(user_id: UUID) -> str:
    return create_access_token(user_id)


@pytest_asyncio.fixture
async def refresh_token_data(
    test_user: UserDB,
    fake_redis: FakeRedis
    ) -> str:
    token, jti, family_id = create_refresh_token(test_user.id)
    ttl_seconds = int(settings.REFRESH_TOKEN_EXPIRE_DAYS.total_seconds())

    await fake_redis.set(
        f"refresh_token:{jti}", 
        family_id,
        ex=ttl_seconds
        )
    await fake_redis.sadd(
        f"user_tokens:{test_user.id}", jti
    )

    return {
        "token": token,
        "jti": jti,
        "family_id": family_id,
        "user_id": test_user.id
    }


#@pytest_asyncio.fixture
#async def user_repo(session: AsyncSession) -> UserService:
#    return UserRepository(session)
#@pytest_asyncio.fixture
#async def user_service(user_repo: UserRepository) -> UserService:
#    return UserService(user_repo)


@pytest_asyncio.fixture
async def test_user(
    session: AsyncSession
    ) -> UserDB:
    user = UserDB(**test_user_data)
    user.id = uuid4()

    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_publisher(
    session: AsyncSession
    ) -> UserDB:
    user = UserDB(**test_user_data)
    user.roles = [UserRole.USER, UserRole.PUBLISHER]
    user.id = uuid4()

    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user
