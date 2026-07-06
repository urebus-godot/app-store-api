from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis
import pytest

from app.models.user import UserDB


class TestLogin:
    async def test_login(
        self, client: AsyncClient, test_user: UserDB
    ):  
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "testUser", "password": "testPassword"}
            )
        data = response.json()

        assert response.status_code == 200
        assert data["user_id"] == str(test_user.id)
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(
        self, client: AsyncClient
    ):  
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "testUser", "password": "TestPassword"}
            )

        assert response.status_code == 401

    @pytest.mark.skip
    async def test_logout(
        self, client: AsyncClient, refresh_token_data: dict[str, str]
    ):  
        token = refresh_token_data["token"]
        response = await client.post(
            f"/api/v1/users/logout?refresh_token={token}",
            #params=token
            )
        data = response.json()

        assert response.status_code == 200
        assert "message" in data


class TestRefresh:
    async def test_refresh_tokens(
        auth_client: AsyncClient, 
        refresh_token_data: dict[str, str],
        fake_redis: FakeRedis
    ):
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]
        response = await auth_client.post(
            f"/api/v1/users/refresh?refresh_token={token}"
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

        assert await fake_redis.exists(f"blacklist:{jti}")

