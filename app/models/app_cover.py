from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import TIMESTAMP


class AppCover(SQLModel, table=True):
    __tablename__ = "app_covers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    app_id: UUID = Field(foreign_key="apps.id", index=True)
    object_key: str
    position: int = Field(default=0)
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )
