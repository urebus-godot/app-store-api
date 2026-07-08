from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis
import pytest

from app.models.user import UserDB

class TestUsers:
    async def test_get_current_user(
        self, auth_client: AsyncClient
    ):
        response = await auth_client.get(
            "/api/v1/users/me"
        )
        data = response.json()
        assert response.status_code == 200
        assert "password" not in data
        assert data["username"] == "testUser"

    async def test_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users",
            json={"username": "myuser", "password": "12345"}
        )
        assert response.status_code == 201
        assert response.json()["username"] is not None

    @pytest.mark.parametrize(
        argnames=[
            "update_data", "expected_data", "expected_status_code"
            ], 
        argvalues=[
            [{"username": "ureb"}, {"username": "ureb"}, 200],
            [{"balance": "10000"}, {"balance": "0"}, 200],
            [{"name": "serega"}, {"username": "testUser"}, 200]
        ]
    )
    async def test_update_user(
        self, 
        auth_client: AsyncClient, 
        update_data: dict,
        expected_data: dict,
        expected_status_code: int
    ):
        response = await auth_client.patch(
            f"/api/v1/users/me",
            json=update_data
        )
        data = response.json()
        assert response.status_code == expected_status_code

        for key in expected_data.keys():
            assert data[key] == expected_data[key]

    async def test_delete_current_user(
        self, 
        auth_client: AsyncClient, 
        test_user: UserDB,
        fake_redis: FakeRedis
    ):
        delete_response = await auth_client.delete(
            "/api/v1/users/me"
            )
        assert delete_response.status_code == 204
        assert not await fake_redis.exists(f"user_tokens:{test_user.id}")

        get_response = await auth_client.get(
            f"/api/v1/users/{test_user.id}"
            )
        assert get_response.status_code == 404
