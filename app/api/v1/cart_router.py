from uuid import UUID

from fastapi import APIRouter, status, BackgroundTasks

from app.core.tasks import send_email
from app.core.config import settings
from app.dependencies import (
    CartServiceDep,
    UserIdDep,
    UserDep,
    SkipLimitParams,
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
    app_id: UUID, user_id: UserIdDep, cart_service: CartServiceDep
) -> CartItemResponse:
    return await cart_service.add_app_to_cart(app_id, user_id)


@router.post("/carts/checkout")
async def purchase_apps_in_cart(
    user: UserDep, cart_service: CartServiceDep, bg_tasks: BackgroundTasks
) -> list[AppResponse]:
    if user.email is not None:
        bg_tasks.add_task(
            send_email,
            [str(user.email)],
            "Purchase receipt",
            settings.RECEIPT_TEMPLATE,
        )
    return await cart_service.purchase_apps_in_cart(user)


@router.post("/carts/{user_id}")
async def get_cart(
    user_id: UserIdDep, cart_service: CartServiceDep
) -> CartResponse:
    cart = await cart_service.get_or_create_cart(user_id)
    total_price = sum([item.app.price for item in cart.items])
    cart_response = CartResponse(
        id=cart.id, items=cart.items, total_price=total_price
    )
    await cart_service.cart_repo.session.commit()
    return cart_response


@router.get("/purchase_history")
async def get_purchases_history(
    skip_limit: SkipLimitParams,
    user_id: UserIdDep,
    cart_service: CartServiceDep,
) -> list[PurchaseResponse]:
    skip, limit = skip_limit
    purchases = await cart_service.get_purchase_history(user_id, skip, limit)
    return purchases


@router.delete(
    "/carts/{user_id}/{app_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_app_from_cart(
    app_id: UUID, user_id: UserIdDep, cart_service: CartServiceDep
) -> None:
    await cart_service.remove_app_from_cart(app_id, user_id)


@router.delete("carts/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(user_id: UserIdDep, cart_service: CartServiceDep) -> None:
    await cart_service.clear_cart(user_id)
