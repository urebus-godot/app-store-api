from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis
import pytest

from app.models.user import UserDB
from app.core.logging import logger


class TestLogin:
    async def test_login(
        self, 
        client: AsyncClient, 
        test_user: UserDB, 
        fake_redis: FakeRedis
    ):  
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "testUser", "password": "testPassword"}
            )
        data = response.json()

        assert response.status_code == 200
        assert data["user_id"] == str(test_user.id)
        assert await fake_redis.exists(f"user_tokens:{test_user.id}")

    async def test_login_wrong_password(
        self, client: AsyncClient, test_user: UserDB
    ):  
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "testUser", "password": "TestPassword"}
            )

        assert response.status_code == 401

    async def test_logout(
        self, 
        auth_client: AsyncClient, 
        refresh_token_data: dict[str, str],
        test_user: UserDB,
        fake_redis: FakeRedis
    ):  
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]
        response = await auth_client.post(
            f"/api/v1/users/logout?refresh_token={token}",
            #params=token
            )
        data = response.json()

        assert response.status_code == 200
        assert "message" in data
        assert await fake_redis.exists(f"blacklist:{jti}")
        assert not await fake_redis.exists(f"refresh_token:{jti}")


class TestRefresh:
    async def test_refresh_tokens(
        self,
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

    async def test_refresh_tokens_revoke(
        self,
        auth_client: AsyncClient, 
        refresh_token_data: dict[str, str],
        test_user: UserDB,
        fake_redis: FakeRedis
    ):
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]

        response = await auth_client.post(
            f"/api/v1/users/refresh?refresh_token={token}"
        )
        
        repeat_response = await auth_client.post(
            f"/api/v1/users/refresh?refresh_token={token}"
        )
        repeat_data = repeat_response.json()

        assert response.status_code == 200
        assert repeat_data["detail"] == "Token reuse detected. All sessions revoked"
        assert await fake_redis.exists(f"blacklist:{jti}")
        assert not await fake_redis.exists(f"user_tokens:{test_user.id}")