from decimal import Decimal
from uuid import UUID, uuid4

from httpx import AsyncClient
from fastapi.responses import JSONResponse

from redis.asyncio import Redis
from app.uow.orm import UnitOfWork
from app.core.exceptions import (
    insufficient_funds_exception,
    invalld_promo_code_exception
)
from app.repo.finance_repo import FinanceRepository
from app.repo.user_repo import UserRepository

from app.schemas.finance import TransferRequest
from app.models.finance import TransferDB
from app.base_models.finance import CurrencyType


class FinanceService:
    def __init__(
        self, 
        finance_repo: FinanceRepository,
        user_repo: UserRepository,
        uow: UnitOfWork
    ):
        self.finance_repo = finance_repo
        self.user_repo = user_repo
        self.uow = uow

    async def create_promo_code(
        self, 
        data: dict[str, str],
        expire: int, 
        redis: Redis
    ) -> str:
        code = uuid4()
        await redis.set(
            name=f"promo_codes:{code}",
            value=data,
            ex=expire
            )
        return str(code)

    async def process_promo_code(
        self, 
        user_id: UUID,
        code: UUID, 
        redis: Redis
    ) -> dict[str, Decimal]:
        async with self.uow:
            amount = await redis.get(name=f"promo_codes:{code}")

            if amount is None:
                raise invalld_promo_code_exception

            amount = Decimal(amount)
            user = await self.uow.user_repo.get_user_by_id(user_id)
            user.balance += amount

            await redis.delete(f"promo_codes:{code}")
            await self.uow.commit()

        return {"balance": user.balance, "amount_received": amount}

    async def create_transfer_to_balance(
        self, data: TransferRequest, user_id: UUID
    ) -> dict[str, Decimal]:
        """Increase user's balance and create row in the db for transfer."""
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)
            result = await self.uow.finance_repo.create_transfer_to_balance(
                data, user
                )
            await self.uow.commit()

        return result

    async def create_transfer_to_card(
        self, data: TransferRequest, user_id: UUID
    ) -> dict[str, Decimal]:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)
            if user.balance < data.amount:
                raise insufficient_funds_exception
            
            result = await self.uow.finance_repo.create_transfer_to_card(
                data, user
                )
            await self.uow.commit()

        return result

    async def get_transfers(
        self, 
        user_id: UUID,
        skip: int, limit: int
    ) -> list[TransferDB]:
        transfers = await self.finance_repo.get_transfers(
            user_id, skip, limit
            )
        return transfers

    async def convert_rubles(
        self, 
        amount: float, 
        to_currency: CurrencyType,
        api_client: AsyncClient
    ) -> Decimal | JSONResponse:
        """Makes call to external API to convert 
        funds from rubles to specified currency"""
        if to_currency == CurrencyType.RUB or amount == 0.0:
            return round(Decimal(amount), 2)

        api_response = await api_client.get(
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
