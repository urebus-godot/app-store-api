from uuid import UUID
from decimal import Decimal

from app.core.exceptions import (
    not_enough_funds_exception,
    app_purchased_exception,
    app_in_cart_exception,
    app_published_exception,
    empty_cart_exception,
    app_not_in_cart_exception)
from app.core.logging import logger
from app.repo.cart_repo import CartRepository
from app.service.app_service import AppService
from app.models.user import UserDB
from app.models.app import AppDB


class CartService:
    def __init__(
        self, app_service: AppService, cart_repo: CartRepository
    ):
        self.cart_repo = cart_repo
        self.app_service = app_service

    async def get_or_create_cart(
        self, user_id: UUID
    ):
        return await self.cart_repo.get_or_create_cart(user_id)

    async def add_app_to_cart(
        self, id: UUID, user: UserDB
    ) -> dict[str, str]:
        app = await self.app_service.get_app(id)
        user_cart = await self.get_or_create_cart(user.id)

        if app in user.purchased_apps:
            raise app_purchased_exception

        if app in user_cart.items:
            raise app_in_cart_exception

        if app in user.published_apps:
            raise app_published_exception

        return await self.cart_repo.add_app_to_cart(
            user=user, app=app
            )

    async def purchase_apps_in_cart(
        self, user: UserDB
    ) -> list[AppDB]:
        cart = await self.get_or_create_cart(user.id)

        if not cart.items:
            raise empty_cart_exception

        purchased_apps = []
        try:
            for item in cart.items:
                if item.app in user.purchased_apps:
                    continue
                await self.cart_repo.add_purchase(user.id, item)
                purchased_apps.append(item.app)

            for item in cart.items:
                await self.session.delete(item)

            self.cart_repo.session.commit()

        except Exception as e:
            await self.cart_repo.session.rollback()
            logger.error(f"An error occurred during transaction: {e}")

        return purchased_apps

    async def remove_app_from_cart(
        self, id: UUID, user: UserDB
    ) -> dict[str, str]:
        app = await self.app_service.get_app(id)
        user_cart = await self.get_or_create_cart(user.id)

        if app not in user_cart.items:
            raise app_not_in_cart_exception

        return await self.cart_repo.remove_app_from_cart(
            user=user, app=app
            )