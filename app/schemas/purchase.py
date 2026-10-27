from datetime import datetime
from uuid import UUID
from decimal import Decimal

from sqlmodel import SQLModel, Field
from pydantic import ConfigDict, field_serializer


class PurchaseResponse(SQLModel):
    id: UUID
    app_id: UUID
    purchased_at: datetime
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        return round(float(value), 2)


class CartItemResponse(SQLModel):
    id: UUID
    app_id: UUID
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(SQLModel):
    id: UUID
    items: list["CartItemResponse"] = []
    total_price: Decimal = Field(default=0.0, ge=0.0)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_price")
    def serialize_total_price(self, value: Decimal) -> float:
        return round(float(value), 2)
