from functools import lru_cache

from redis.asyncio import from_url as redis_from_url
from redis.asyncio import Redis
from redis import from_url as sync_redis_from_url

from app.core.config import settings


class RedisClient:
    def __init__(self, url: str):
        self.redis = redis_from_url(url, decode_responses=True)

    async def close_conn(self) -> None:
        await self.redis.aclose()


class SyncRedisClient:
    def __init__(self, url: str):
        self.redis = sync_redis_from_url(url, decode_responses=True)

    def close_conn(self) -> None:
        self.redis.aclose()


def connect_to_redis_client(url: str = settings.REDIS_URL) -> RedisClient:
    return RedisClient(url)


def connect_to_sync_redis_client(
    url: str = settings.REDIS_URL
) -> SyncRedisClient:
    return SyncRedisClient(url)


def get_redis() -> Redis:
    from app.main import app
    return app.state.redis_client.redis
