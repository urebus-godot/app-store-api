from datetime import datetime, timezone, date
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, DATE
from sqlalchemy import String

from app.models.purchase import PurchaseDB
from app.base_models.user import BaseUser, UserRole


class UserDB(BaseUser, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )

    hashed_password: str
    roles: list["UserRole"] = Field(
        sa_type=ARRAY(String), default=[UserRole.USER]
    )

    registered_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )
    birth_date: Optional[date] = Field(
        default=None,
        sa_type=DATE()
        )
    
    balance: Decimal = Field(default=0, ge=0)

    cart: Optional["CartDB"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    purchased_apps: list["AppDB"] = Relationship(
        back_populates="users_purchased", link_model=PurchaseDB
    )
    published_apps: list["AppDB"] = Relationship(
        back_populates="publisher",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    reviews: list["ReviewDB"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    discussions: list["DiscussionDB"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    messages: list["MessageDB"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    transfers: list["TransferDB"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    ) 