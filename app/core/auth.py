from uuid import uuid4
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jwt import PyJWTError
import jwt

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import (
    invalid_refresh_token_exception,
    invalid_access_token_exception
    )
from app.db.redis import Redis

def create_access_token(
    user_id: str,
) -> str:
    """Create a JWT access token for the user."""
    expire = datetime.now(timezone.utc) + settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    payload = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "type": "access"
    }

    return jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )


async def create_refresh_token(
    user_id: str, redis: Redis
) -> str:
    """Create a refresh token for the user."""
    jti = str(uuid4())
    family_id = str(uuid4())
    expire = datetime.now(timezone.utc) + settings.REFRESH_TOKEN_EXPIRE_DAYS

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "jti": jti,
        "family_id": family_id
    }

    refresh_token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
        )
    
    refresh_ttl = int(settings.REFRESH_TOKEN_EXPIRE_DAYS.total_seconds())

    await redis.set(
        name=f"refresh_token:{jti}",
        value=family_id, 
        ex=refresh_ttl
    )
    await redis.sadd(f"user_tokens:{user_id}", jti)
    await redis.expire(f"user_tokens:{user_id}", refresh_ttl)

    return refresh_token


async def create_token_pair(
    user_id: str, redis: Redis
) -> dict[str, str]:
    """Create both access and refresh tokens for the user."""
    logger.info(f"{redis.connection_pool.connection_kwargs=}")
    access_token = create_access_token(user_id)
    refresh_token = await create_refresh_token(user_id, redis)
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token
        }


async def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
            )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise invalid_access_token_exception


async def revoke_all_user_tokens(
    user_id: str, redis: Redis
) -> None:
    """Adds all user's refresh tokens to the blacklist in Redis"""
    jtis = await redis.smembers(f"user_tokens:{user_id}")
    for jti in jtis:
        jti_str = jti.decode() if isinstance(jti, bytes) else jti
        ttl = await redis.ttl(f"refresh_token:{jti_str}")

        if ttl > 0:
            await redis.set(
                f"blacklist:{jti_str}", "1", ex=ttl
                )
        await redis.delete(f"refresh_token:{jti_str}")

    await redis.delete(f"user_tokens:{user_id}")


async def refresh_tokens(
    refresh_token: str, redis: Redis
) -> dict[str, str]:
    """Creates new refresh and access tokens 
    if the refresh token is not blacklisted."""
    try:
        payload = jwt.decode(
            refresh_token, 
            settings.SECRET_KEY, 
            algorithms=settings.JWT_ALGORITHM
            )
        logger.info(f"Decoded refresh token: \n {payload = }")
    except PyJWTError:
        raise invalid_refresh_token_exception

    if payload.get("type") != "refresh":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong token type"
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")
    family_id = payload.get("family_id")

    token_blacklisted = await redis.exists(f"blacklist:{jti}")

    if token_blacklisted:
        await revoke_all_user_tokens(user_id, redis)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token reuse detected. All sessions revoked"
        )
    logger.info(f"Looking for family with key: 'refresh_token:{jti}' \nvalue={await redis.get(f"refresh_token:{jti}")}")
    stored_family = await redis.get(f"refresh_token:{jti}")
    logger.info(f"{stored_family = }")
    logger.info(f"{family_id = }")
    if stored_family is None or stored_family != family_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token not found or invalid"
        )

    remaining_ttl = await redis.ttl(f"refresh_token:{jti}")
    await redis.set(
        f"blacklist:{jti}", "1", 
        ex=max(remaining_ttl, 1)
        )
    logger.info(f"Redis set blacklist: {await redis.exists(f"blacklist:{jti}")}")
    await redis.delete(f"refresh_token:{jti}")
    logger.info(f"Redis is deleting 'refresh_token:{jti}' key-value pair")

    new_tokens = await create_token_pair(user_id, redis)
    return new_tokens
