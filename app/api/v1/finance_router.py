from decimal import Decimal
from uuid import UUID
from typing import Annotated, Any, Union

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from app.schemas.finance import TransferRequest, TransferResponse
from app.base_models.finance import CurrencyType

from app.api.deps import (
    UserDep, 
    UserIdDep, 
    FinanceServiceDep, 
    rate_limit, 
    SkipLimitParams,
    RedisDep,
    get_finance_api_client
    )

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post("/transfers/balance")
async def top_up_balance(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> TransferResponse:
    """Increases user's balance by specified amount 
    and adds transfer to the database.
    
    *Returns*: TransferResponse object"""
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
    """Increases user's balance and deletes the promo code
    if it is stored in the Redis.

    *Returns*: dict object containing new user's balance 
    and received balance"""
    return await finance_service.process_promo_code(
        user_id, promo_code, redis
        )


@router.post("/transfers/withdrawal")
async def withdraw_funds_to_card(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> TransferResponse:
    """Simulates a transfer from the user balance to a card linked 
    to the user and adds it to the database.

    *Returns*: TransferResponse object"""
    return await finance_service.create_transfer_to_card(data, user_id)


@router.get(
    "/transfers/history",
    response_model=list[TransferResponse]
)
async def get_transfer_history(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    finance_service: FinanceServiceDep
) -> list[TransferResponse]:
    """Fetches the current user's transfers from the database.

    *Returns*: list of TransferResponse objects"""
    return await finance_service.get_transfers(user_id, *skip_limit)


@router.get(
    "/finance/me/balance",
    response_model=Union[dict[str, Any], JSONResponse]
)
async def get_balance(
    user: UserDep,
    finance_service: FinanceServiceDep,
    finance_api_client: Annotated[
        AsyncClient, Depends(get_finance_api_client)
    ],
    currency: CurrencyType = CurrencyType.RUB,
) -> dict[str, Any] | JSONResponse:
    """Calls an external API to convert the user's balance 
    from rubles to the specified currency.
    
    *Returns*: dict object containing the user's 
    balance in the specified currency if the call was successful; 
    otherwise, returns JSONResponse object with details."""
    result = await finance_service.convert_rubles(
        float(user.balance), 
        currency, 
        finance_api_client
    )
    if isinstance(result, Decimal):
        return {"balance": result, "currency": currency}
    else:
        return result
