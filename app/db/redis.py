from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

class RedisConnection:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL, decode_responses=True
            )

    async def set(self, key: str, value) -> None:
        await self.redis.set(key, value)
        await self.redis.aclose()

    async def get(self, key: str) -> Any:
        await self.redis.get(key)
        await self.redis.aclose()

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
        await self.redis.aclose()