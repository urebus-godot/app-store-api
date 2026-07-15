from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from enum import StrEnum

from sqlmodel import SQLModel, Field


class OperationType(StrEnum):
    BALANCE_TOP_UP: str = "balance top-up"
    WITHDRAWAL_TO_CARD: str = "withdrawal to card"


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
    operation_type: OperationType


class TransferResponse(BaseTransfer):
    made_at: datetime
    operation_type: OperationType
