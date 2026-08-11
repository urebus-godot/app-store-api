from app.core.config import settings

settings.WORKER_DB_URL = settings.TEST_WORKER_DB_URL

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime, timezone, date
import asyncio

from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker
    )
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

from httpx import ASGITransport, AsyncClient
from fakeredis.aioredis import FakeRedis
from fakeredis import FakeServer
import pytest_asyncio
import jwt

from app.models.user import UserDB, UserRole
from app.models.app import AppDB, GameGenre

from app.db.postgres import get_session
from app.api.dependencies import (
    get_current_user, 
    get_current_user_id, 
    get_redis, 
    can_send_email, 
    get_refresh_secret_key,
    get_access_secret_key,
    rate_limit,
    get_session_factory
    )

from app.core.security import get_password_hash
from app.core.logging import logger
from app.main import app


test_user_data = {
    "username": "testUser",
    "hashed_password": get_password_hash("testPassword"),
    "email": "user@example.com",
    "birth_date": date(year=1980, month=4, day=1)
}

# ----- Tokens -----

def create_access_token(
    user_id: UUID,
    expires_delta: datetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    #extra_claims: Optional[dict[str, str]] = None,
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "type": "access"
    }

    return jwt.encode(
        payload, 
        settings.TEST_ACCESS_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    user_id: UUID,
    jti: UUID = uuid4(),
    family_id: UUID = uuid4(),
    expires_delta: datetime = settings.REFRESH_TOKEN_EXPIRE_DAYS,
) -> tuple[str, str, str]:
    """Returns refresh token, jti, family_id"""
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": str(jti),
        "family_id": str(family_id),
    }
    token = jwt.encode(
        payload, 
        settings.TEST_REFRESH_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return str(token), str(jti), str(family_id)


@pytest_asyncio.fixture(scope="session")
async def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="logger")
def get_logger():
    return logger


# ----- Database fixtures -----

engine = create_async_engine(settings.TEST_DB_URL)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_connection():
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            yield connection
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
def session_factory(db_connection):
    return async_sessionmaker(
        bind=db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint" 
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def fake_redis() -> AsyncGenerator[FakeRedis, None, None]:
    redis = FakeRedis(server=FakeServer())
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest_asyncio.fixture(scope="function", autouse=True)
def setup_test_celery():
    from app.task_queue.celery_app import celery_app
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://"
    )


# ----- Client fixtures -----

def override_general_deps(
    db_session: AsyncSession, 
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis,
    ignore_rate_limit: bool = True
    ) -> None:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_redis] = lambda: fake_redis 
    app.dependency_overrides[can_send_email] = lambda: False
    app.dependency_overrides[get_refresh_secret_key] = (
        lambda: settings.TEST_REFRESH_SECRET_KEY
        )
    app.dependency_overrides[get_access_secret_key] = (
        lambda: settings.TEST_ACCESS_SECRET_KEY
        )
    if ignore_rate_limit:
        app.dependency_overrides[rate_limit] = lambda: True


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, 
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis
):
    override_general_deps(
        db_session, 
        session_factory,
        fake_redis
        )

    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://tests"
        ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_client(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis,
    test_user: UserDB,
    access_token: str,
    refresh_token_data: dict[str, str],
):
    override_general_deps(
        db_session,
        session_factory,
        fake_redis
    )
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_current_user_id] = lambda: test_user.id


    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport,
        base_url="http://tests",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_token_data["token"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_client_2(
    auth_client: AsyncClient,
    test_user_2: UserDB
):
    app.dependency_overrides[get_current_user] = lambda: test_user_2
    app.dependency_overrides[get_current_user_id] = lambda: test_user_2.id
    auth_client.headers = {
        "Authorization": 
        f"Bearer {create_access_token(test_user_2.id)}"
        }
    yield auth_client


@pytest_asyncio.fixture
async def real_auth_client(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis,
    access_token: str,
    refresh_token_data: dict[str, str],
):
    override_general_deps(
        db_session, 
        session_factory,
        fake_redis,
        )

    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport,
        base_url="http://tests",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_token_data["token"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def publisher_client(
    db_session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis,
    test_publisher: UserDB,
    access_token: str,
):
    override_general_deps(db_session, session_factory, fake_redis)
    app.dependency_overrides[get_current_user] = lambda: test_publisher
    app.dependency_overrides[get_current_user_id] = lambda: test_publisher.id

    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport,
        base_url="http://tests",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def rate_limited_client(
    db_session: AsyncSession, 
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis
):
    override_general_deps(
        db_session, 
        session_factory,
        fake_redis,
        False
        )

    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://tests"
        ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def rate_limited_auth_client(
    db_session: AsyncSession, 
    session_factory: async_sessionmaker[AsyncSession],
    fake_redis: FakeRedis,
    test_user: UserDB,
    access_token: str
):
    override_general_deps(
        db_session, 
        session_factory,
        fake_redis, 
        False
        )
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


# ----- Token fixtures -----

@pytest_asyncio.fixture
def access_token(test_user: UserDB) -> str:
    return create_access_token(test_user.id)


@pytest_asyncio.fixture
async def refresh_token_data(test_user: UserDB, fake_redis: FakeRedis) -> dict:
    token, jti, family_id = create_refresh_token(test_user.id)
    ttl_seconds = int(settings.REFRESH_TOKEN_EXPIRE_DAYS.total_seconds())

    await fake_redis.set(f"refresh_token:{jti}", family_id, ex=ttl_seconds)
    await fake_redis.sadd(f"user_tokens:{test_user.id}", jti)

    return {
        "token": token,
        "jti": jti,
        "family_id": family_id,
        "user_id": test_user.id,
    }


@pytest_asyncio.fixture
async def user_data() -> dict[str, str]:
    return test_user_data


# ----- Test user fixtures -----

@pytest_asyncio.fixture(scope="function")
async def test_user(
    db_session: AsyncSession
) -> UserDB:
    user = UserDB(**test_user_data)

    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_2(db_session: AsyncSession) -> UserDB:
    user = UserDB(
        username="anotherUser",
        hashed_password="testPassword2",
        roles=[UserRole.PUBLISHER],
    )

    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def test_publisher(
    test_user: UserDB, db_session: AsyncSession
) -> UserDB:
    test_user.roles = [UserRole.USER, UserRole.PUBLISHER]

    await db_session.flush()
    await db_session.refresh(test_user)

    return test_user


# ----- App fixtures -----

@pytest_asyncio.fixture(scope="function")
async def test_app(db_session: AsyncSession, test_publisher: UserDB) -> AppDB:
    app = AppDB(
        title="test app",
        description="test desc",
        price=300,
        publisher_id=test_publisher.id,
        keywords=["paid", "test", "app"],
    )
    db_session.add(app)
    await db_session.flush()
    await db_session.refresh(app)

    return app


@pytest_asyncio.fixture(scope="function")
async def test_app_2(db_session: AsyncSession, test_user_2: UserDB) -> AppDB:
    app = AppDB(
        title="test app 2",
        description="test desc for test app",
        price=0,
        publisher_id=test_user_2.id,
        keywords=["free", "app", "test"],
    )
    db_session.add(app)
    await db_session.flush()
    await db_session.refresh(app)

    return app


@pytest_asyncio.fixture(scope="function")
async def test_app_2_paid(
    db_session: AsyncSession, test_user_2: UserDB
) -> AppDB:
    app = AppDB(
        title="my paid app",
        description="This is a simple app for testing purposes",
        price=1000,
        publisher_id=test_user_2.id,
        keywords=["paid", "app", "test"],
    )
    db_session.add(app)
    await db_session.flush()
    await db_session.refresh(app)

    return app


@pytest_asyncio.fixture(scope="function")
async def test_app_private(
    db_session: AsyncSession, test_user_2: UserDB
) -> AppDB:
    app = AppDB(
        title="my private app",
        description="test description",
        price=0,
        publisher_id=test_user_2.id,
        keywords=["free", "app", "test"],
        public=False,
    )
    db_session.add(app)
    await db_session.flush()
    await db_session.refresh(app)

    return app


@pytest_asyncio.fixture(scope="function")
async def test_game(db_session: AsyncSession, test_user_2: UserDB):
    game = AppDB(
        title="game1",
        description="test game",
        price=1000,
        publisher_id=test_user_2.id,
        keywords=["paid", "game", "test"],
        category="game",
        genre=GameGenre.ADVENTURE
    )
    db_session.add(game)
    await db_session.flush()
    await db_session.refresh(game)

    return game


@pytest_asyncio.fixture(scope="function")
async def test_apps(db_session: AsyncSession, test_user_2: UserDB):
    apps = [
        AppDB(
            title="test", 
            keywords=[" KEY ", " key 2"], 
            publisher_id=test_user_2.id
            ),
        AppDB(
            title="test", 
            keywords=["kEy"],
            publisher_id=test_user_2.id
            ),
        AppDB(
            title="test", 
            keywords=["  key  "],
            publisher_id=test_user_2.id
            ),
        AppDB(
            title="test", 
            keywords=[" Newkey "],
            publisher_id=test_user_2.id
            ),
        AppDB(
            title="hidden test", 
            keywords=[" Newkey "],
            publisher_id=test_user_2.id,
            public=False
            )
        ]
    db_session.add_all(apps)
    await db_session.flush()
    for app in apps:
        await db_session.refresh(app)

    return apps
