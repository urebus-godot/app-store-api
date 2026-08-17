from datetime import timedelta

from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis

from app.models.user import UserDB
from tests.conftest import create_refresh_token


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
        refresh_token_data["token"]
        jti = refresh_token_data["jti"]
        response = await real_auth_client.post("/api/v1/users/logout")
        data = response.json()
        print(f"\n\n{data=}\n\n")
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
        logger
    ):
        refresh_token_data["token"]
        jti = refresh_token_data["jti"]
        logger.error("\n\n\n\nSending request...")
        response = await real_auth_client.post("/api/v1/users/refresh")
        logger.error("\nResponse: \n\n", response.json())
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
        refresh_token_data["token"]
        jti = refresh_token_data["jti"]

        response = await real_auth_client.post("/api/v1/users/refresh")

        repeat_response = await real_auth_client.post("/api/v1/users/refresh")
        repeat_data = repeat_response.json()

        assert response.status_code == 200
        assert (
            repeat_data["detail"]
            == "Token reuse detected. All sessions revoked"
        )
        assert await fake_redis.exists(f"blacklist:{jti}")
        assert not await fake_redis.exists(f"user_tokens:{test_user.id}")

    async def test_refresh_tokens_expired(
        self,
        real_auth_client: AsyncClient,
        test_user: UserDB,
        fake_redis: FakeRedis
    ):
        token, _, _ = create_refresh_token(
            test_user.id,
            expires_delta=timedelta(seconds=0)
            )
        response = await real_auth_client.post(
            "/api/v1/users/refresh",
            cookies={"refresh_token": token}
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    async def test_get_current_user_no_auth(
        self,
        client: AsyncClient,
        test_user: UserDB
    ):
        response = await client.get(
            "/api/v1/users/me"
        )
        assert response.status_code == 401

    async def test_get_current_user_wrong_token_type(
        self,
        client: AsyncClient,
        refresh_token_data: dict[str, str],
    ):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {refresh_token_data["token"]}"}
        )
        assert response.status_code == 401