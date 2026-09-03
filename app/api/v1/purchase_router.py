from uuid import UUID

from fastapi import APIRouter, status, BackgroundTasks, Depends

from app.api.deps import (
    PurchaseServiceDep,
    UserIdDep,
    UserDep,
    SkipLimitParams,
    SendEmailDep,
    rate_limit
)
from app.schemas.purchase import (
    CartResponse,
    CartItemResponse,
    PurchaseResponse,
)
from app.schemas.app import AppResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/carts/my/{app_id}", 
    status_code=status.HTTP_201_CREATED
    )
async def add_app_to_cart(
    app_id: UUID,
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> CartItemResponse:
    return await purchase_service.add_app_to_cart(app_id, user_id)


@router.post("/carts/checkout")
async def purchase_apps_in_cart(
    user: UserDep,
    bg_tasks: BackgroundTasks,
    purchase_service: PurchaseServiceDep,
    sends_email: SendEmailDep
) -> list[AppResponse]:
    if sends_email:
        return await purchase_service.purchase_apps_in_cart(
            user_id=user.id, user_email=user.email, bg_tasks=bg_tasks
            )
    return await purchase_service.purchase_apps_in_cart(
        user_id=user.id, user_email=None, bg_tasks=bg_tasks
        )


@router.post("/carts/my")
async def get_cart(
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> CartResponse:
    cart = await purchase_service.get_cart_for_user(user_id)
    return cart


@router.get("/purchases/my/history")
async def get_purchase_history(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    purchase_service: PurchaseServiceDep,
) -> list[PurchaseResponse]:
    purchases = await purchase_service.get_purchase_history(
        user_id, *skip_limit
    )
    return purchases


@router.delete(
    "/carts/my/{app_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_app_from_cart(
    app_id: UUID,
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> None:
    await purchase_service.remove_item_from_cart(app_id, user_id)


@router.delete(
    "/carts/my", 
    status_code=status.HTTP_204_NO_CONTENT
    )
async def clear_cart(
    user_id: UserIdDep,
    purchase_service: PurchaseServiceDep
) -> None:
    await purchase_service.delete_cart_by_user(user_id)
