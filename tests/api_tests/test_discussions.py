import asyncio
from logging import Logger

from httpx import AsyncClient

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from httpx_ws.transport import ASGIWebSocketTransport
from httpx_ws import aconnect_ws
import httpx

from fakeredis import FakeRedis

import pytest_asyncio

from app.core.config import settings

from app.main import app
from app.api.dependencies import get_redis, get_access_secret_key, get_session, get_session_factory, rate_limit

from app.models.discussion import DiscussionDB, MessageDB
from app.models.user import UserDB
from app.models.app import AppDB


@pytest_asyncio.fixture(scope="function")
async def ws_client(
    fake_redis: FakeRedis, 
    test_discussion_2: DiscussionDB, 
    test_user: UserDB,
    db_session: AsyncSession, 
    session_factory: async_sessionmaker[AsyncSession],
    logger: Logger
):
    transport = ASGIWebSocketTransport(app)
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[
        get_access_secret_key
        ] = lambda: settings.TEST_ACCESS_SECRET_KEY
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    #app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[rate_limit] = lambda: True
    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://ws_test"
        ) as ac:
            
            yield ac
    except RuntimeError as e:
        logger.error(f"Runtime error occurred: {e}")


@pytest_asyncio.fixture
async def test_discussion(
    test_user: UserDB, test_app: AppDB, db_session: AsyncSession
):
    discussion = DiscussionDB(
        topic="This is a test topic",
        creator_id=test_user.id,
        app_id=test_app.id,
    )

    test_messages = [
        MessageDB(
            text=[
                "Test",
                "Message",
                "This is test msg",
                "Just test",
                "Msg Test",
            ][i % 5],
            author_id=test_user.id,
            discussion_id=discussion.id,
        )
        for i in range(10)
    ]

    db_session.add(discussion)
    db_session.add_all(test_messages)
    await db_session.flush()
    await db_session.refresh(discussion)

    return discussion


@pytest_asyncio.fixture
async def test_discussion_2(
    test_user_2: UserDB, test_app: AppDB, db_session: AsyncSession
):
    discussion = DiscussionDB(
        topic="This is a test topic",
        creator_id=test_user_2.id,
        app_id=test_app.id,
    )
    db_session.add(discussion)
    await db_session.flush()
    await db_session.refresh(discussion)

    return discussion


@pytest_asyncio.fixture
async def test_message(
    test_user: UserDB, test_discussion: DiscussionDB, db_session: AsyncSession
):
    message = MessageDB(
        text="This is a test message",
        author_id=test_user.id,
        discussion_id=test_discussion.id,
    )
    db_session.add(message)
    await db_session.flush()
    await db_session.refresh(message)

    return message


class TestDiscussion:
    async def test_create_discussion(
        self, auth_client: AsyncClient, test_app: AppDB
    ):
        diss_response = await auth_client.post(
            f"/api/v1/discussions/{test_app.id}",
            json={"topic": "This app is questionable"},
        )
        data = diss_response.json()

        assert diss_response.status_code == 201
        assert data["topic"] == "This app is questionable"

    async def test_create_discussion_app_not_exists(
        self, auth_client: AsyncClient
    ):
        response = await auth_client.post(
            "/api/v1/discussions/097c51bc-3c31-4cdf-b726-a4b1df084d8e",
            json={"topic": "test topic"},
        )

        assert response.status_code == 404

    async def test_get_discussions(
        self, auth_client: AsyncClient, test_discussion: DiscussionDB
    ):
        response = await auth_client.get(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data["messages"]) == 10

    async def test_get_app_discussions(
        self,
        auth_client: AsyncClient,
        test_app: AppDB,
        test_discussion: DiscussionDB,
    ):
        response = await auth_client.get(
            f"/api/v1/discussions/app/{test_app.id}"
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert "topic" in data[0]

    async def test_get_my_discussions(
        self, auth_client: AsyncClient, test_discussion: DiscussionDB
    ):
        response = await auth_client.get("/api/v1/discussions/user/me")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert "topic" in data[0]

    async def test_delete_discussion(
        self, auth_client: AsyncClient, test_discussion: DiscussionDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        assert delete_response.status_code == 204

        get_response = await auth_client.get(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_discussion_no_rights(
        self, auth_client: AsyncClient, test_discussion_2: DiscussionDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/discussions/{test_discussion_2.id}"
        )
        assert delete_response.status_code == 403

    async def test_delete_discussion_not_exists(
        self, auth_client: AsyncClient
    ):
        delete_response = await auth_client.delete(
            "/api/v1/discussions/399848f1-a846-4f82-ac3e-aa3caf7394ee"
        )
        assert delete_response.status_code == 404


class TestMessage:
    async def test_create_message(
        self, auth_client: AsyncClient, test_discussion: DiscussionDB
    ):
        msg_response = await auth_client.post(
            f"/api/v1/discussions/{test_discussion.id}/messages",
            json={"text": "Another test message for a test discussion."},
        )
        assert msg_response.status_code == 201

    async def test_create_message_diss_not_exists(
        self, auth_client: AsyncClient
    ):
        msg_response = await auth_client.post(
            "/api/v1/discussions/"
            "399848f1-a846-4f82-ac3e-aa3caf7394ee/messages",
            json={"text": "Another test message for a test discussion."},
        )
        assert msg_response.status_code == 404

    async def test_delete_message(
        self,
        auth_client: AsyncClient,
        test_discussion: DiscussionDB,
        test_message: MessageDB,
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/discussions/messages/{test_message.id}"
        )
        assert delete_response.status_code == 204

        get_response = await auth_client.get(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        assert get_response.status_code == 200
        assert len(get_response.json()["messages"]) == 10

    async def test_ws_discussion(
        self,
        ws_client: AsyncClient,
        access_token: str,
        test_discussion_2: DiscussionDB
    ):
        async with aconnect_ws(
            f"/api/v1/ws/discussions/{test_discussion_2.id}",
            ws_client
        ) as websocket:
            await websocket.send_json({"type": "auth", "token": access_token})
            data = await asyncio.wait_for(websocket.receive_json(), timeout=1)
            assert data == {"type": "auth_ok"}
            
            await asyncio.sleep(0.1) 

            await websocket.send_json({"text": "Hello, World!"})
            raw_response = await asyncio.wait_for(websocket.receive_json(), timeout=1)

            assert "Hello, World!" in str(raw_response)