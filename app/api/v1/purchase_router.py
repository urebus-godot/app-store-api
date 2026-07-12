from uuid import UUID

from fastapi import APIRouter, status, BackgroundTasks

from app.core.tasks import send_email
from app.core.config import settings
from app.dependencies import (
    PurchaseServiceDep,
    UserIdDep,
    UserDep,
    SkipLimitParams,
    UnitOfWorkDep
)
from app.models.purchase import (
    CartResponse,
    CartItemResponse,
    PurchaseResponse,
)
from app.models.app import AppResponse

router = APIRouter()


@router.post("/carts/{user_id}/{app_id}", status_code=status.HTTP_201_CREATED)
async def add_app_to_cart(
    app_id: UUID, 
    user_id: UserIdDep, 
    purchase_service: PurchaseServiceDep,
    uow: UnitOfWorkDep
) -> CartItemResponse:
    return await purchase_service.add_app_to_cart(
        app_id, user_id, uow
        )


@router.post("/carts/checkout")
async def purchase_apps_in_cart(
    user: UserDep, 
    bg_tasks: BackgroundTasks,
    purchase_service: PurchaseServiceDep,
    uow: UnitOfWorkDep
) -> list[AppResponse]:
    if user.email is not None:
        bg_tasks.add_task(
            send_email,
            [str(user.email)],
            "Purchase receipt",
            settings.RECEIPT_TEMPLATE,
        )
    return await purchase_service.purchase_apps_in_cart(user, uow)


@router.post("/carts/{user_id}")
async def get_cart(
    user_id: UserIdDep, 
    purchase_service: PurchaseServiceDep,
    uow: UnitOfWorkDep
) -> CartResponse:
    cart = await purchase_service.get_or_create_cart(user_id, uow)
    total_price = sum([item.app.price for item in cart.items])
    cart_response = CartResponse(
        id=cart.id, items=cart.items, total_price=total_price
    )
    return cart_response


@router.get("/purchases/history")
async def get_purchase_history(
    user_id: UserIdDep, 
    skip_limit: SkipLimitParams,
    purchase_service: PurchaseServiceDep
) -> list[PurchaseResponse]:
    purchases = await purchase_service.get_purchase_history(
        user_id, *skip_limit
        )
    return purchases


@router.delete(
    "/carts/{user_id}/{app_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_app_from_cart(
    app_id: UUID, 
    user_id: UserIdDep, 
    purchase_service: PurchaseServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await purchase_service.remove_app_from_cart(app_id, user_id, uow)


@router.delete("carts/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    user_id: UserIdDep, 
    purchase_service: PurchaseServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await purchase_service.clear_cart(user_id, uow)
