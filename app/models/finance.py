from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from sqlmodel import SQLModel, Field


class BaseTransfer(SQLModel):
    amount: Decimal = Field(gt=0)


class TransferRequest(BaseTransfer):
    pass


class TransferDB(BaseTransfer, table=True):
    __tablename__ = "transfers"

    id: UUID = Field(
        primary_key=True, default_factory=uuid4
        )
    user_id: UUID = Field(foreign_key="users.id")
    made_at: datetime = Field(
        default_factory=lambda: datetime.now()
        )


class TransferResponse(BaseTransfer):
    made_at: datetime
