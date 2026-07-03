from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import ASGITransport, AsyncClient
import pytest

from app.models.user import UserDB, UserRequest
from app.db.postgres import get_session
from app.db.redis import Redis, RedisClient, get_redis_client
from app.dependencies import (
    get_current_user, get_current_user_id
    )
from app.core.auth import create_access_token
from app.service.user_service import UserService
from app.repo.user_repo import UserRepository
from app.core.config import settings
from app.main import app

test_user_data = {
    "username": "testUser", 
    "password": "testPassword", 
    "email": "ureb588@gmail.com"
    }

test_engine = create_async_engine(settings.TEST_DB_URL)

# Run services for tests: docker compose -f compose.test.yaml up -d

async def get_test_session() -> AsyncGenerator[AsyncSession, None, None]:
    async with AsyncSession(
        bind=test_engine, expire_on_commit=False
        ) as session:
        yield session


async def get_test_redis_client() -> Redis:
    return RedisClient(settings.TEST_REDIS_URL).redis


async def get_test_user_id() -> UUID:
    user = UserDB()
    return user


async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def clear_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture()
async def client():
    transport = ASGITransport(app)
    async with AsyncClient(
            transport
            =transport, base_url="http://tests"
            ) as ac:
        yield ac

        app.dependency_overrides[get_session] = get_test_session
        app.dependency_overrides[get_redis_client] = get_test_redis_client
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_user_id] = get_test_user_id

    app.dependency_overrides.clear()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None, None]:
    async with AsyncSession(
            bind=test_engine, expire_on_commit=False
            ) as session:
        yield session


@pytest.fixture
async def user_repo(session: AsyncSession) -> UserService:
    return UserRepository(session)


@pytest.fixture
async def user_service(user_repo: UserRepository) -> UserService:
    return UserService(user_repo)


@pytest.fixture
async def test_user(
    user_service: UserService
    ) -> UserDB:
    await setup_db()

    user = await user_service.get_user(username=test_user_data["username"])
    if not user:
        user_request = UserRequest.model_validate(test_user_data)
        user = await user_service.register_user(user_request)
    return user


@pytest.fixture
def auth_header(test_user: UserDB):
    access_token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {access_token}"}