from uuid import uuid4
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

import jwt

from app.utils.time import get_refresh_token_expire

from app.core.config import settings
from app.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)
from app.db.redis import Redis

logger = logging.getLogger("core.auth")


def create_access_token(
    data: dict, 
    secret_key: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token for the user."""
    payload = data.copy()
    expires_delta = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update(
        {"exp": int(expire.timestamp()), "type": "access"}
    )
    return jwt.encode(
        payload, secret_key, algorithm=settings.JWT_ALGORITHM
    )


async def create_refresh_token(
    user_id: str, secret_key: str, redis: Redis
) -> str:
    """Create a refresh token for the user."""
    jti = str(uuid4())
    family_id = str(uuid4())
    expire = get_refresh_token_expire()

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "jti": jti,
        "family_id": family_id,
    }

    refresh_token = jwt.encode(
        payload, secret_key, algorithm=settings.JWT_ALGORITHM
    )
    days = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_ttl = int(days.total_seconds())

    await redis.set(
        name=f"refresh_token:{jti}", value=family_id, ex=refresh_ttl
    )
    await redis.sadd(f"user_tokens:{user_id}", jti)
    await redis.expire(f"user_tokens:{user_id}", refresh_ttl)

    return refresh_token


async def create_token_pair(
    data: dict, redis: Redis,
    access_secret_key: str,
    refresh_secret_key: str
) -> dict[str, str]:
    """Create both access and refresh tokens for the user."""
    access_token = create_access_token(data, access_secret_key)
    refresh_token = await create_refresh_token(
        data["sub"], refresh_secret_key, redis
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


def decode_access_token(
    token: str, secret_key: str
) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, 
            secret_key, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()


async def revoke_all_user_tokens(user_id: str, redis: Redis) -> None:
    """Adds all user's refresh tokens to the blacklist in Redis"""
    jtis = await redis.smembers(f"user_tokens:{user_id}")
    for jti in jtis:
        jti_str = jti.decode() if isinstance(jti, bytes) else jti
        ttl = await redis.ttl(f"refresh_token:{jti_str}")

        if ttl > 0:
            await redis.set(f"blacklist:{jti_str}", "1", ex=ttl)
        await redis.delete(f"refresh_token:{jti_str}")

    await redis.delete(f"user_tokens:{user_id}")
