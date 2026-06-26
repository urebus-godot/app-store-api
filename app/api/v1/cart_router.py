from uuid import UUID

from fastapi import APIRouter

from app.dependencies import CartServiceDep, UserDep
from app.models.app_purchase import CartResponse

router = APIRouter()


@router.post("/cart/{id}/add-to-cart")
async def add_app_to_cart(
    id: UUID,
    user: UserDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.add_app_to_cart(id, user)


@router.post("/cart/purchase-apps")
async def purchase_apps_in_cart(
    user: UserDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.purchase_apps_in_cart(
        user
        )


@router.get("/cart")
async def get_cart(
    user: UserDep,
    cart_service: CartServiceDep
) -> CartResponse:
    cart = await cart_service.get_or_create_cart(user.id)
    total_price = sum([item.app.price for item in cart.items])
    return CartResponse(
        id=cart.id, items=cart.items, total_price=total_price
        )


@router.delete("/cart/{id}/remove-app")
async def remove_app_from_cart(
    id: UUID,
    user: UserDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.remove_app_from_cart(id, user)