from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP


class AppArchive(SQLModel, table=True):
    __tablename__ = "app_archives"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    filename: str
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    app_id: UUID = Field(foreign_key="apps.id")
    app: "AppDB" = Relationship(back_populates="archive")


class AppCover(SQLModel, table=True):
    __tablename__ = "app_covers"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    extension: str
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    app_id: UUID = Field(foreign_key="apps.id")
    app: "AppDB" = Relationship(back_populates="covers")


class AppThumbnail(SQLModel, table=True):
    __tablename__ = "app_thumbnails"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    extension: str
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    app_id: UUID = Field(foreign_key="apps.id")
    app: "AppDB" = Relationship(back_populates="thumbnails")


class UserProfilePicture(SQLModel, table=True):
    __tablename__ = "user_profile_pictures"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    user_id: UUID = Field(foreign_key="users.id")
    extension: str