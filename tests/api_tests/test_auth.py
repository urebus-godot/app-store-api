from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis

from app.models.user import UserDB


class TestLogin:
    async def test_login(
        self, client: AsyncClient, test_user: UserDB, fake_redis: FakeRedis
    ):
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "testUser", "password": "testPassword"},
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
            data={"username": "testUser", "password": "TestPassword"},
        )

        assert response.status_code == 401

    async def test_logout(
        self,
        real_auth_client: AsyncClient,
        refresh_token_data: dict[str, str],
        test_user: UserDB,
        fake_redis: FakeRedis,
    ):
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]
        response = await real_auth_client.post(
            f"/api/v1/users/logout"
        )
        data = response.json()

        assert response.status_code == 200
        assert "message" in data
        assert await fake_redis.exists(f"blacklist:{jti}")
        assert not await fake_redis.exists(f"refresh_token:{jti}")


class TestRefresh:
    async def test_refresh_tokens(
        self,
        real_auth_client: AsyncClient,
        refresh_token_data: dict[str, str],
        fake_redis: FakeRedis,
    ):
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]

        response = await real_auth_client.post(
            f"/api/v1/users/refresh"
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()
        assert await fake_redis.exists(f"blacklist:{jti}")

    async def test_refresh_tokens_revoke(
        self,
        real_auth_client: AsyncClient,
        refresh_token_data: dict[str, str],
        test_user: UserDB,
        fake_redis: FakeRedis,
    ):
        token = refresh_token_data["token"]
        jti = refresh_token_data["jti"]

        response = await real_auth_client.post(
            "/api/v1/users/refresh"
        )

        repeat_response = await real_auth_client.post(
            "/api/v1/users/refresh"
        )
        repeat_data = repeat_response.json()

        assert response.status_code == 200
        assert (
            repeat_data["detail"]
            == "Token reuse detected. All sessions revoked"
        )
        assert await fake_redis.exists(f"blacklist:{jti}")
        assert not await fake_redis.exists(f"user_tokens:{test_user.id}")
