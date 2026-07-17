from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends

from app.models.finance import TransferRequest, TransferResponse, CurrencyType
from app.dependencies import (
    UserDep, UserIdDep, FinanceServiceDep, rate_limit, UnitOfWorkDep
    )

router = APIRouter(
    dependencies=[Depends(rate_limit)]
    )


@router.post("/transfers/balance")
async def top_up_balance(
    data: TransferRequest,
    user: UserDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer_to_balance(data, user)


@router.post("/transfers/withdrawal")
async def withdraw_funds_to_card(
    data: TransferRequest,
    user: UserDep,
    finance_service: FinanceServiceDep,
    uow: UnitOfWorkDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer_to_card(data, user, uow)


@router.get("/transfers/history")
async def get_transfer_history(
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> list[TransferResponse]:
    return await finance_service.get_transfers(user_id)



@router.post("/finance/me/balance")
async def get_balance(
    user: UserDep,
    currency: CurrencyType,
    finance_service: FinanceServiceDep
    ) -> dict[str, Any]:
    """Returns current user's balance measured in the specified currency."""
    result = await finance_service.convert_rubles(
        float(user.balance), currency
        )
    if isinstance(result, Decimal):
        return {"balance": result, "currency": currency, "base_currency": "RUB"}
    else:
        return result
