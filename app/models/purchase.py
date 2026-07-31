from datetime import datetime, timezone
from uuid import UUID, uuid4
from decimal import Decimal

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP


class PurchaseDB(SQLModel, table=True):
    __tablename__ = "purchases"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    purchased_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    app_id: UUID = Field(foreign_key="apps.id", primary_key=True)

    price: Decimal


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    added_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )

    cart_id: UUID = Field(foreign_key="carts.id", ondelete="CASCADE")
    app_id: UUID = Field(foreign_key="apps.id", ondelete="CASCADE")

    cart: "CartDB" = Relationship(back_populates="items")
    app: "AppDB" = Relationship()


class CartDB(SQLModel, table=True):
    __tablename__ = "carts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        foreign_key="users.id", unique=True, ondelete="CASCADE"
    )
    user: "UserDB" = Relationship(back_populates="cart")
    items: list["CartItem"] = Relationship(
        back_populates="cart",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )