from decimal import Decimal

from fastapi import APIRouter, Depends

from app.models.finance import TransferRequest, TransferResponse
from app.dependencies import (
    UserDep, UserIdDep, FinanceServiceDep, rate_limit
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
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer_to_card(data, user)


@router.get("/transfers/history")
async def get_transfer_history(
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> list[TransferResponse]:
    return await finance_service.get_transfers(user_id)