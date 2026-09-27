from uuid import UUID

from fastapi import APIRouter, status, BackgroundTasks, Depends

from app.api.deps import (
    PurchaseServiceDep,
    UserIdDep,
    UserDep,
    SkipLimitParams,
    rate_limit
)
from app.schemas.purchase import (
    CartResponse,
    CartItemResponse,
    PurchaseResponse,
)
from app.schemas.app import AppResponse, GameResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/carts/my/{app_id}", 
    status_code=status.HTTP_201_CREATED,
    tags=["Carts"],
    response_model=CartItemResponse
)
async def add_app_to_cart(
    app_id: UUID,
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> CartItemResponse:
    """Создаёт товар для корзины пользователя в базе данных, 
    связанный с указанным приложением.
    
    **Возвращает**: CartItemResponse."""
    return await purchase_service.add_app_to_cart(app_id, user_id)


@router.post(
    "/carts/checkout", 
    tags=["Carts"], 
    response_model=list[AppResponse | GameResponse]
)
async def purchase_apps_in_cart(
    user: UserDep,
    bg_tasks: BackgroundTasks,
    purchase_service: PurchaseServiceDep
) -> list[AppResponse | GameResponse]:
    """Приобетение всех приложений, добавленных в корзину пользователя,
    если на балансе достаточно средств, и создание покупок в базе данных.
    
    **Возращает**: list[AppResponse | GameResponse] 
    (список приобретённых приложений)."""
    return await purchase_service.purchase_apps_in_cart(
        user_id=user.id, bg_tasks=bg_tasks
        )


@router.post(
    "/carts/my", 
    tags=["Carts"], 
    response_model=CartResponse
)
async def get_cart(
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> CartResponse:
    """Ищет корзину пользователя сначала в кеше, затем в базе данных,
    или создаёт её при отсутствии.
    
    **Возращает**: CartResponse."""
    cart = await purchase_service.get_cart_for_user(user_id)
    return cart


@router.get(
    "/purchases/my/history", 
    tags=["Purchases"],
    response_model=list[PurchaseResponse]
)
async def get_purchase_history(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    purchase_service: PurchaseServiceDep,
) -> list[PurchaseResponse]:
    """Находит все покупки пользователя в базе данных.
    
    **Возращает**: list[PurchaseResponse]."""
    purchases = await purchase_service.get_purchase_history(
        user_id, *skip_limit
    )
    return purchases


@router.delete(
    "/carts/my/{app_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Carts"]
)
async def remove_app_from_cart(
    app_id: UUID,
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> None:
    """Удаляет товар корзины пользователя, 
    связанный с указанным приложением, из базы данных.
    
    **Возращает**: None."""
    await purchase_service.remove_item_from_cart(app_id, user_id)


@router.delete(
    "/carts/my", 
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Carts"]
    )
async def clear_cart(
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> None:
    """Удаляет корзину пользователя из базы данных.
    
    **Возращает**: None."""
    await purchase_service.delete_cart_by_user(user_id)
