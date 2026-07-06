from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func
from pydantic import ConfigDict

class Purchase(SQLModel, table=True):
    __tablename__ = "purchases"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )
    purchased_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    #user: "UserDB" = Relationship(back_populates="purchased_apps")

    app_id: UUID = Field(foreign_key="apps.id", primary_key=True)
    #app: "AppDB" = Relationship(back_populates="purchases")

    price: Decimal = Field(ge=0.0)


class PurchaseResponse(SQLModel):
    id: UUID
    purchased_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True
        )

    added_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now()
        )
    )

    cart_id: UUID = Field(foreign_key="carts.id", ondelete="CASCADE")
    app_id: UUID = Field(foreign_key="apps.id", ondelete="CASCADE")

    cart: Cart = Relationship(
        back_populates="items"
    )    
    app: "AppDB" = Relationship()


class CartItemResponse(SQLModel):
    id: UUID
    app_id: UUID
    #app: "AppResponse"
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


#class BaseCart(SQLModel):
 #   id: UUID
  #  items: list["CartItem"]


class Cart(SQLModel, table=True):
    __tablename__ = "carts"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
    )
    user_id: UUID = Field(
        foreign_key="users.id", 
        unique=True, 
        ondelete="CASCADE"
        )
    user: "UserDB" = Relationship(back_populates="cart")
    items: list["CartItem"] = Relationship(
        back_populates="cart",
        cascade_delete=True
    )


class CartResponse(SQLModel):
    id: UUID
    items: list["CartItemResponse"] = []
    total_price: Decimal = Field(default=0.0, ge=0.0)

    model_config = ConfigDict(from_attributes=True)