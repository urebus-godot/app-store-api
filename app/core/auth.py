import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

from app.core.config import settings

# Simple in-memory token blacklist store
# In production, use Redis or a database
blacklisted_tokens: dict[str, datetime] = {}

# Refresh token store (in production, use database)
refresh_tokens: dict[str, dict] = {}  # token -> {"username": str, "exp": datetime}

# JWT Security
security = OAuth2PasswordBearer(tokenUrl="/api/v1/login")#HTTPBearer()

def create_access_token(
    username: str,
) -> str:
    """Create a JWT access token for the user."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,  # Subject (user identifier)
        "exp": int(expire.timestamp()),  # Expiration time as Unix timestamp
        "iat": int(
            datetime.now(timezone.utc).timestamp()
        ),  # Issued at as Unix timestamp
        "jti": secrets.token_urlsafe(16),  # JWT ID (unique identifier)
        "type": "access",  # Token type
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    username: str,
) -> str:
    """Create a refresh token for the user."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_EXPIRE_DAYS)

    refresh_token = secrets.token_urlsafe(32)

    # Store refresh token info
    refresh_tokens[refresh_token] = {"username": username, "exp": expire}

    # Clean up expired refresh tokens
    cleanup_expired_refresh_tokens()

    return refresh_token


def create_token_pair(username: str) -> tuple[str, str]:
    """Create both access and refresh tokens for the user."""
    access_token = create_access_token(username)
    refresh_token = create_refresh_token(username)
    return access_token, refresh_token


def validate_refresh_token(refresh_token: str) -> str:
    """Validate refresh token and return username."""
    if refresh_token not in refresh_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    token_info = refresh_tokens[refresh_token]

    # Check if token is expired
    if token_info["exp"] < datetime.now(timezone.utc):
        # Remove expired token
        del refresh_tokens[refresh_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired"
        )

    return token_info["username"]


def revoke_refresh_token(refresh_token: str) -> None:
    """Revoke a refresh token (for logout)."""
    if refresh_token in refresh_tokens:
        del refresh_tokens[refresh_token]


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        # Check if token is blacklisted
        if token in blacklisted_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        # Decode the token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def blacklist_token(token: str) -> None:
    """Add token to blacklist (for logout functionality)."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            blacklisted_tokens[token] = exp_datetime

            # Clean up expired blacklisted tokens
            cleanup_expired_blacklisted_tokens()
    except jwt.InvalidTokenError:
        # If token is invalid, no need to blacklist
        pass


def cleanup_expired_blacklisted_tokens() -> None:
    """Remove expired tokens from blacklist to prevent memory leaks."""
    current_time = datetime.now(timezone.utc)
    expired_tokens = [
        token
        for token, exp_time in blacklisted_tokens.items()
        if exp_time < current_time
    ]

    for token in expired_tokens:
        del blacklisted_tokens[token]


def cleanup_expired_refresh_tokens() -> None:
    """Remove expired refresh tokens to prevent memory leaks."""
    current_time = datetime.now(timezone.utc)
    expired_tokens = [
        token for token, info in refresh_tokens.items() if info["exp"] < current_time
    ]

    for token in expired_tokens:
        del refresh_tokens[token]