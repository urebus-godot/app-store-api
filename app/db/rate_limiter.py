import time
import uuid
from typing import Literal
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import settings

LUA_RATE_LIMITER_SCRIPT = """
local key = KEYS[1]

local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_limit = tonumber(ARGV[3])
local member = ARGV[4]

if now == nil or window == nil or request_limit == nil then
    return redis.error_reply("invalid numeric argument passed to script")
end

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
    scope: str


class RateLimiter:
    def __init__(
        self,
        redis: Redis,
        script: str = LUA_RATE_LIMITER_SCRIPT
    ):
        self.redis = redis
        self.script = self.redis.register_script(script)

    async def check(
        self, 
        identifier: str,    
        scope: Literal["user", "ip"],    
        window_seconds: int = settings.WINDOW_SECONDS, 
        limit: int = settings.REQUEST_LIMIT,
    ) -> RateLimitResult:
        key = f"rate_limit:{scope}:{identifier}"
        now = time.time()
        member = f"{now}:{uuid.uuid4().hex}"

        allowed, remaining_requests = await self.script(
            keys=[key],
            args=[now, window_seconds, limit, member]
        )

        return RateLimitResult(
            allowed=bool(allowed),
            remaining_requests=remaining_requests,
            scope=scope
        )
