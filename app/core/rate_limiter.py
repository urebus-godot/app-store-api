from app.core.config import settings
from app.db.redis import get_redis

LUA_SCRIPT = """
local key = KEYS[1]
local arg = ARGV[1]

"""


class RateLimiter:
    def __init__(self):
        self._redis = get_redis()
        self._script = self._redis.register_script(LUA_SCRIPT)

    def is_limited(self):
        self._script()
        settings.WINDOW
        settings.REQUESTS_LIMIT