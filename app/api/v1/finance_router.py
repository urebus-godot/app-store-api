from decimal import Decimal

from fastapi import APIRouter

from app.models.finance import TransferRequest, TransferResponse
from app.dependencies import UserDep, UserIdDep, FinanceServiceDep


router = APIRouter()


@router.post("/transfers/balance")
async def top_up_balance(
    data: TransferRequest,
    user: UserDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer(data, user)


@router.get("/transfers/history")
async def get_transfer_history(
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> list[TransferResponse]:
    return await finance_service.get_transfers(user_id)