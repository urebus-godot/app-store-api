from decimal import Decimal
from uuid import UUID

from httpx import AsyncClient
from fastapi.responses import JSONResponse
from fastapi import status

from app.uow.unit_of_work import UnitOfWork
from app.core.exceptions import insufficient_funds_exception
from app.repo.finance_repo import FinanceRepository
from app.models.finance import TransferRequest, TransferDB, CurrencyType
from app.models.user import UserDB


class FinanceService:
    def __init__(self, finance_repo: FinanceRepository):
        self.finance_repo = finance_repo

    async def create_transfer_to_balance(
        self, data: TransferRequest, user: UserDB
    ) -> dict[str, Decimal]:
        """Increase user's balance and create row in the db for transfer."""
        result = await self.finance_repo.create_transfer_to_balance(
            data, user
            )
        return result

    async def create_transfer_to_card(
        self, data: TransferRequest, user: UserDB, uow: UnitOfWork
    ) -> dict[str, Decimal]:
        if user.balance < data.amount:
            raise insufficient_funds_exception
        
        result = await uow.finance_repo.create_transfer_to_card(
            data, user
            )
        return result

    async def get_transfers(
        self, user_id: UUID
    ) -> list[TransferDB]:
        transfers = await self.finance_repo.get_transfers(user_id)
        return transfers

    async def convert_rubles(
        self, amount: float, to_currency: CurrencyType
    ) -> Decimal | JSONResponse:
        async with AsyncClient(base_url="https://api.frankfurter.dev/v2") as ac:
            api_response = await ac.get(
                "/rates",
                params={"quotes": to_currency, "base": "RUB"}
                )
            data = api_response.json()
            if api_response.status_code >= 400:
                return JSONResponse(
                    data,
                    api_response.status_code
                )
            
            rate = data[0]["rate"]
            converted_amount = amount * rate

        return round(Decimal(converted_amount), 2)
