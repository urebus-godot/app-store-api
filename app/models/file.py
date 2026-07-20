from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


class AppArchive(SQLModel, table=True):
    __tablename__ = "app_archives"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    filename: str
    app_id: UUID = Field(foreign_key="apps.id")
    app: "AppDB" = Relationship(back_populates="archive")


class AppCover(SQLModel, table=True):
    __tablename__ = "app_covers"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    extension: str
    app_id: UUID = Field(foreign_key="apps.id")
    app: "AppDB" = Relationship(back_populates="covers")


class UserProfilePicture(SQLModel, table=True):
    __tablename__ = "user_profile_pictures"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    user_id: UUID = Field(foreign_key="users.id")
    extension: str