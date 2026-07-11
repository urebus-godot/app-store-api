from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from sqlmodel import SQLModel, Field, DateTime, Column, func


class BaseTransfer(SQLModel):
    amount: Decimal = Field(gt=0)


class TransferRequest(BaseTransfer):
    pass


class TransferDB(BaseTransfer):
    id: UUID = Field(
        primary_key=True, 
        default_factory=uuid4
        )
    made_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )


class TransferResponse(BaseTransfer):
    made_at: datetime