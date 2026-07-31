from decimal import Decimal
from enum import StrEnum

from sqlmodel import SQLModel, Field


class OperationType(StrEnum):
    BALANCE_TOP_UP: str = "balance top-up"
    WITHDRAWAL_TO_CARD: str = "withdrawal to card"


class CurrencyType(StrEnum):
    RUB: str = "RUB"
    EUR: str = "EUR"
    USD: str = "USD"
    GBP: str = "GBP"


class BaseTransfer(SQLModel):
    amount: Decimal = Field(gt=0)