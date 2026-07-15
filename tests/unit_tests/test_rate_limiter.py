from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis

from app.core.config import settings
from app.models.user import UserDB


class TestRateLimiter:
    async def test_rate_limit(
        self,
        rate_limited_client: AsyncClient,
        fake_redis: FakeRedis,
        logger
    ):
        logger.info(f"Start Rate Limit Test")
        requests_count = settings.REQUEST_LIMIT
        for _ in range(requests_count):
            response = await rate_limited_client.get(
                "/api/v1/apps"
            )
            logger.info(f"\n\n\n\n{response.json() = }\n\n\n\n")
            assert response.status_code == 200

        limited_response = await rate_limited_client.get(
            "/api/v1/apps"
        )
        remaining = limited_response.headers.get("X-RateLimit-Remaining", "0")
        rate_limit_len = await fake_redis.zcard(f"rate_limit:127.0.0.1")
        assert rate_limit_len == settings.REQUEST_LIMIT
        assert remaining == "0"
        assert limited_response.status_code == 429

    async def test_rate_limit_user(
        self,
        rate_limited_auth_client: AsyncClient,
        fake_redis: FakeRedis,
        test_user: UserDB,
        logger
    ):
        requests_count = settings.REQUEST_LIMIT
        for _ in range(requests_count):
            response = await rate_limited_auth_client.get(
                "/api/v1/users/me"
            )
            assert response.status_code == 200

        limited_response = await rate_limited_auth_client.get(
            "/api/v1/users/me"
        )
        remaining = limited_response.headers.get("X-RateLimit-Remaining", "0")
        assert remaining == "0"
        assert limited_response.status_code == 429