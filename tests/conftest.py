from collections.abc import AsyncGenerator
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime, timezone
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
from fakeredis.aioredis import FakeRedis
import pytest_asyncio
import jwt

from app.models.user import UserDB, UserRole
from app.models.app import AppDB
from app.db.postgres import get_session
from app.dependencies import (
    get_current_user, get_current_user_id, get_redis
    )
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import logger
from app.main import app

test_user_data = {
    "username": "testUser", 
    "hashed_password": get_password_hash("testPassword"), 
    "email": "ureb588@gmail.com",
    #"id": uuid4()#UUID('3076dfdd-fba4-4b11-a415-143ca0e8d21c')
    }


# ----- Tokens -----

def create_access_token(
    user_id: UUID,
    expires_delta: datetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    extra_claims: Optional[dict[str, str]] = None
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "type": "access",
        #"jti": str(uuid4),
        **(extra_claims or {})
    }

    return jwt.encode(
        payload, 
        settings.TEST_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )


def create_refresh_token(
    user_id: UUID, 
    jti: UUID = uuid4(),
    family_id: UUID = uuid4(),
    expires_delta: datetime = settings.REFRESH_TOKEN_EXPIRE_DAYS
) -> tuple[str, str, str]:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": str(jti),
        "family_id": str(family_id)
    }
    token = jwt.encode(
        payload, 
        settings.TEST_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )
    return str(token), str(jti), str(family_id)


#@pytest_asyncio.fixture(scope="session")
#async def event_loop():
#    loop = asyncio.new_event_loop()
#    yield loop
#    loop.close()

@pytest_asyncio.fixture(name="logger")
def get_logger():
    return logger


# ----- Database fixtures -----

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(settings.TEST_DB_URL)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    engine: AsyncEngine
) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            async with AsyncSession(
                bind=connection, 
                expire_on_commit=False
            ) as session:
                
                yield session

            await transaction.rollback()


@pytest_asyncio.fixture
async def fake_redis() -> AsyncGenerator[FakeRedis, None]:
    redis = FakeRedis()
    yield redis
    await redis.flushall()
    await redis.aclose()


# ----- Client fixtures -----

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


@pytest_asyncio.fixture
async def auth_client(
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


@pytest_asyncio.fixture
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
async def publisher_client(
    db_session: AsyncSession, 
    fake_redis: FakeRedis,
    test_publisher: UserDB, 
    access_token: str
):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_current_user] = lambda: test_publisher
    app.dependency_overrides[get_current_user_id] = lambda: test_publisher.id

    transport = ASGITransport(app)
    async with AsyncClient(
            transport=transport, 
            base_url="http://tests",
            headers={"Authorization": f"Bearer {access_token}"}
            ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ----- Token fixtures -----

@pytest_asyncio.fixture
def access_token(test_user: UserDB) -> str:
    return create_access_token(test_user.id)


@pytest_asyncio.fixture
async def refresh_token_data(
    test_user: UserDB,
    fake_redis: FakeRedis
    ) -> dict:
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


@pytest_asyncio.fixture
async def user_data() -> dict[str, str]:
    return test_user_data


# ----- Test user fixtures -----

@pytest_asyncio.fixture
async def test_user(
    db_session: AsyncSession
    ) -> UserDB:
    user = UserDB(**test_user_data)

    db_session.add(user)
    await db_session.commit()
    #await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_user_2(
    db_session: AsyncSession
    ) -> UserDB:
    user = UserDB(
        username="anotherUser", 
        hashed_password="12345",
        roles=[UserRole.PUBLISHER]
        )

    db_session.add(user)
    await db_session.commit()
    #await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_publisher(
    test_user: UserDB, db_session: AsyncSession
    ) -> UserDB:
    test_user.roles = [UserRole.USER, UserRole.PUBLISHER]

    db_session.add(test_user)
    await db_session.commit()
    #await db_session.refresh(user)
    
    return test_user


# ----- App fixtures -----

@pytest_asyncio.fixture
async def test_app(
    db_session: AsyncSession, test_publisher: UserDB
    ) -> AppDB:
    app = AppDB(
        title="MS Code",
        description="IDE for programming with brainf*ck",
        price=300,
        publisher_id = test_publisher.id,
        keywords=["code", "ms", "bf", "programming", "test", "app"]
    )
    db_session.add(app)
    await db_session.commit()
    #await db_session.refresh(app)

    return app


@pytest_asyncio.fixture
async def test_app_2(
    db_session: AsyncSession, test_user_2: UserDB
    ) -> AppDB:
    app = AppDB(
        title="my app",
        description="This is a simple app for testing purposes, "
            "and it's FREE",
        price=0,
        publisher_id=test_user_2.id,
        keywords=["free", "app", "test"]
    )
    db_session.add(app)
    await db_session.commit()
    #await db_session.refresh(app)

    return app


@pytest_asyncio.fixture
async def test_app_private(
    db_session: AsyncSession, test_user_2: UserDB
    ) -> AppDB:
    app = AppDB(
        title="my private app",
        description="This is a simple app for testing purposes, "
            "and it's FREE but PRIVATE",
        price=0,
        publisher_id=test_user_2.id,
        keywords=["free", "app", "test"],
        public=False
    )
    db_session.add(app)
    await db_session.commit()
    #await db_session.refresh(app)

    return app


@pytest_asyncio.fixture
async def test_apps():
    apps = [
        AppDB()
        for _ in range(40)
    ]

    return apps
