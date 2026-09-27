from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from app.schemas.transfer import TransferRequest, TransferResponse
from app.base_models.transfer import CurrencyType

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


@router.post(
    "/transfers/balance",
    response_model=TransferResponse
)
async def top_up_balance(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> TransferResponse:
    """Пополняет баланс пользователя и создаёт перевод в базе данных.
    
    **Возвращает**: TransferResponse"""
    return await finance_service.create_transfer_to_balance(
        data, user_id
    )


@router.post("/promo_codes")
async def activate_promo_code(
    promo_code: str,
    user_id: UserIdDep,
    redis: RedisDep,
    finance_service: FinanceServiceDep
) -> dict[str, Decimal]:
    """Пополняет баланс пользователя 
    и удаляет промокод из Redi, если он валиден.
    
    **Возвращает**: dict[str, Decimal]"""
    return await finance_service.activate_promo_code(
        user_id, promo_code, redis
    )


@router.post(
    "/transfers/withdrawal",
    response_model=TransferResponse
)
async def withdraw_funds_to_card(
    data: TransferRequest,
    user_id: UserIdDep,
    finance_service: FinanceServiceDep
) -> TransferResponse:
    """Симулирует вывод средств на карту и создаёт перевод в базе данных.
    
    **Возвращает**: TransferResponse"""
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
    """Находит переводы пользователя в базе данных.
    
    **Возвращает**: list[TransferResponse]"""
    return await finance_service.get_transfers(user_id, *skip_limit)


@router.get("/finance/me/balance")
async def get_balance(
    user: UserDep,
    finance_service: FinanceServiceDep,
    finance_api_client: Annotated[
        AsyncClient, Depends(get_finance_api_client)
    ],
    currency: CurrencyType = CurrencyType.RUB,
) -> JSONResponse:
    """Возвращает баланс пользователя.
    
    **Параметры** currency - валюта, в которой измеряется баланс 
    ("RUB", "EUR", "USD", "GBP"). 
    Если указана не "RUB", вызывает внешний API 
    для конвертации валюты из рублей.

    **Возвращает**: JSONResponse"""
    result = await finance_service.convert_rubles(
        float(user.balance), 
        currency, 
        finance_api_client
    )
    if isinstance(result, Decimal):
        return {"balance": result, "currency": currency}
    else:
        return result
