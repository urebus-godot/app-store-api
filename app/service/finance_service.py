from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.repo.finance_repo import FinanceRepository
from app.models.finance import TransferRequest, TransferDB
from app.models.user import UserDB


class FinanceService:
    def __init__(self, finance_repo: FinanceRepository):
        self.finance_repo = finance_repo

    async def create_transfer(
        self, data: TransferRequest, user: UserDB
    ) -> dict[str, Decimal]:
        """Increase user's balance and create row in the db for transfer."""
        result = await self.finance_repo.create_transfer(data, user)
        return result

    async def get_transfers(
        self, user_id: UUID
    ) -> list[TransferDB]:
        transfers = await self.finance_repo.get_transfers(user_id)
        return transfers