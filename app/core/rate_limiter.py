import time
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import settings

LUA_RATE_LIMITER_SCRIPT = """
local key = KEYS[1]

local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

local request_count = redis.call('ZCARD', key)

if request_count < request_limit then
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, window)
    return {1, request_limit - request_count - 1}
else
    return {0, 0}
end
"""

@dataclass
class RateLimitResult:
    allowed: bool
    remaining_requests: int


class RateLimiter:
    def __init__(
        self,
        redis: Redis,
        window_s: int = settings.WINDOW_SECONDS, 
        limit: int = settings.REQUEST_LIMIT,
        script: str = LUA_RATE_LIMITER_SCRIPT
    ):
        self._redis = redis
        self._window_s = window_s
        self._limit = limit
        self._script = self._redis.register_script(script)

    async def check(self, identifier: str):
        key = f"rate_limit:{identifier}"
        now = time.time()
        member = f"{now}:{uuid.uuid4().hex}"

        allowed, remaining_requests = await self._script(
            keys=[key],
            args=[now, self._window_s, self._limit, member]
        )

        return RateLimitResult(
            allowed=bool(allowed),
            remaining_requests=remaining_requests
        )
