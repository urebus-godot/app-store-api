from datetime import datetime, timezone, timedelta

from app.core.config import settings


def days_to_seconds(days: int) -> int:
    return days * 24 * 60 * 60


def get_refresh_token_expire() -> datetime:
    now = datetime.now(timezone.utc)
    return now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def get_time_string(
    date_time: datetime = datetime.now(timezone.utc)
) -> str:
    return date_time.strftime("%Y/%m/%d %H:%M:%S")