from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest_asyncio

from app.models.user import UserDB
from app.models.app import AppDB


class TestCart:
    async def test_add_app_to_cart(
        self, 
        auth_client: AsyncClient, 
        test_app: AppDB,
        test_user: UserDB
    ):
        response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}/{test_app.id}"
        )
        data = response.json()

        assert response.status_code == 201

    async def test_get_cart(
        self, 
        auth_client: AsyncClient, 
        test_discussion: DiscussionDB
    ):
        response = await auth_client.get(
            f"/api/v1/discussions/user/me"
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert "topic" in data[0]

    async def test_delete_discussion(
        self, 
        auth_client: AsyncClient, 
        test_discussion: DiscussionDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        assert delete_response.status_code == 204

        get_response = await auth_client.get(
            f"/api/v1/discussions/{test_discussion.id}"
        )
        assert get_response.status_code == 404
