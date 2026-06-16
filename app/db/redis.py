from redis.asyncio import Redis
from app.core.config import settings

class RedisBackend:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)