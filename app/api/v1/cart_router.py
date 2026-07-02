from uuid import UUID

from fastapi import APIRouter

from app.dependencies import CartServiceDep, UserIdDep, UserDep
from app.models.app_purchase import CartResponse
from app.models.app import AppResponse
from app.core.logging import logger

router = APIRouter()


@router.post("/cart/{id}/add-to-cart")
async def add_app_to_cart(
    id: UUID,
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.add_app_to_cart(id, user_id)


@router.post("/cart/purchase-apps")
async def purchase_apps_in_cart(
    user_id: UserDep,
    cart_service: CartServiceDep
) -> list[AppResponse]:
    return await cart_service.purchase_apps_in_cart(user_id)


@router.get("/cart")
async def get_cart(
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> CartResponse:
    cart = await cart_service.get_or_create_cart(user_id)
    total_price = sum([item.app.price for item in cart.items])
    cart_response = CartResponse(
        id=cart.id, items=cart.items, total_price=total_price
        )
    await cart_service.cart_repo.session.commit()
    return cart_response


@router.delete("/cart/{id}/remove-app")
async def remove_app_from_cart(
    id: UUID,
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.remove_app_from_cart(id, user_id)


@router.delete("users/{user_id}/cart/clear")
async def clear_cart(
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.clear_cart(user_id)