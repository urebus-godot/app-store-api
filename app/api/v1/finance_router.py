from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.finance import TransferRequest, TransferResponse
from app.base_models.finance import CurrencyType

from app.api.dependencies import (
    UserDep, 
    UserIdDep, 
    FinanceServiceDep, 
    rate_limit, 
    SkipLimitParams,
    RedisDep
    )

router = APIRouter(
    dependencies=[Depends(rate_limit)]
    )


@router.post("/transfers/balance")
async def top_up_balance(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer_to_balance(
        data, user_id
        )


@router.post("/promo_codes")
async def enter_promo_code(
    promo_code: UUID,
    user_id: UserIdDep,
    redis: RedisDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    return await finance_service.process_promo_code(
        user_id, promo_code, redis
        )


@router.post("/transfers/withdrawal")
async def withdraw_funds_to_card(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Increases user's balance by specified amount"""
    return await finance_service.create_transfer_to_card(data, user_id)


@router.get("/transfers/history")
async def get_transfer_history(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    finance_service: FinanceServiceDep
) -> list[TransferResponse]:
    return await finance_service.get_transfers(user_id, *skip_limit)


@router.post("/finance/me/balance")
async def get_balance(
    user: UserDep,
    finance_service: FinanceServiceDep,
    currency: CurrencyType = CurrencyType.RUB,
    ) -> JSONResponse:
    """Returns current user's balance measured in the specified currency."""
    result = await finance_service.convert_rubles(
        float(user.balance), currency
        )
    if isinstance(result, Decimal):
        return {"balance": result, "currency": currency}
    else:
        return result
