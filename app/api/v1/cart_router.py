from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies import CartServiceDep, UserIdDep, UserDep
from app.models.app_purchase import CartResponse
from app.models.app import AppResponse
from app.core.logging import logger

router = APIRouter()


@router.post("/carts/{user_id}/{app_id}")
async def add_app_to_cart(
    app_id: UUID,
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> dict[str, str]:
    return await cart_service.add_app_to_cart(app_id, user_id)


@router.get("/carts/{user_id}/apps")
async def purchase_apps_in_cart(
    user_id: UserDep,
    cart_service: CartServiceDep
) -> list[AppResponse]:
    return await cart_service.purchase_apps_in_cart(user_id)


@router.get("/carts/{user_id}")
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


@router.delete(
    "/carts/{user_id}/{app_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_app_from_cart(
    app_id: UUID,
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> None:
    await cart_service.remove_app_from_cart(app_id, user_id)


@router.delete(
    "carts/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def clear_cart(
    user_id: UserIdDep,
    cart_service: CartServiceDep
) -> None:
    await cart_service.clear_cart(user_id)
