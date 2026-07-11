from datetime import datetime, timezone

from app.core.config import settings


def get_refresh_token_expire() -> datetime:
    now = datetime.now(timezone.utc)
    return now + settings.REFRESH_TOKEN_EXPIRE_DAYS
