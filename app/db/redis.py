from redis.asyncio import from_url as redis_from_url
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    def __init__(self, url: str):
        self.redis = redis_from_url(url, decode_responses=True)

    async def close_conn(self) -> None:
        await self.redis.aclose()


def connect_to_redis_client(url: str = settings.REDIS_URL) -> RedisClient:
    return RedisClient(url)


def get_redis() -> Redis:
    from app.main import app

    return app.state.redis_client.redis
