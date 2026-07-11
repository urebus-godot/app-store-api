from uuid import UUID
from typing import Optional

from fastapi import status, HTTPException
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import (
    insufficient_funds_exception,
    app_purchased_exception,
    app_in_cart_exception,
    app_published_exception,
    empty_cart_exception,
    app_not_in_cart_exception,
)
from app.core.logging import logger
from app.repo.purchase_repo import PurchaseRepository
from app.service.app_service import AppService
from app.models.user import UserDB
from app.models.app import AppDB
from app.models.purchase import PurchaseDB, CartItem, CartDB


class PurchaseService:
    def __init__(
        self, 
        redis: Redis,
        app_service: AppService, 
        cart_repo: PurchaseRepository
    ):
        self.redis = redis
        self.cart_repo = cart_repo
        self.app_service = app_service

    async def get_or_create_cart(self, user_id: UUID):
        cached_cart = await self.redis.get(f"cart_cache:{user_id}")

        if cached_cart is not None:
            return CartDB.model_validate_json(cached_cart)

        cart = await self.cart_repo.get_or_create_cart(user_id)

        cached_cart = await self.redis.set(
            name=f"cart_cache:{user_id}",
            value=cart.model_dump_json(),
            ex=settings.CACHE_TTL_SECONDS
            )

        return cart

    async def get_purchase(
        self, app_id: UUID, user_id: UUID
    ) -> Optional[PurchaseDB]:
        purchase = await self.cart_repo.get_purchase(app_id, user_id)
        return purchase

    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ) -> Optional[CartItem]:
        item = await self.cart_repo.get_cart_item(cart_id, app_id)
        return item

    async def get_purchase_history(
        self, user_id: UUID, skip: int, limit: int
    ) -> list[PurchaseDB]:
        purchases = await self.cart_repo.get_purchases(user_id, skip, limit)
        return purchases

    async def add_app_to_cart(
        self, 
        app_id: UUID, user_id: UUID,
    ) -> CartItem:
        user_cart = await self.get_or_create_cart(user_id)
        app = await self.app_service.get_app(app_id)

        purchased = await self.get_purchase(app_id, user_id)
        already_added = await self.get_cart_item(user_cart.id, app_id)
        published = await self.app_service.app_repo.get_app_by_publisher(
            user_id, app_id
        )

        if purchased:
            raise app_purchased_exception
        
        if already_added:
            raise app_in_cart_exception
        
        if published:
            raise app_published_exception

        await self.redis.delete(f"cart_cache:{user_id}")

        return await self.cart_repo.add_app_to_cart(user_cart, app_id)

    async def purchase_apps_in_cart(
        self, user: UserDB
    ) -> list[AppDB]:
        cart = await self.get_or_create_cart(user.id)
        total_price = sum([item.app.price for item in cart.items])

        if not cart.items:
            raise empty_cart_exception
        
        if user.balance < total_price:
            raise insufficient_funds_exception

        purchased_apps = []
        try:
            for item in cart.items:
                purchased = await self.get_purchase(item.app_id, user.id)
                if purchased:
                    continue
                
                await self.cart_repo.add_purchase(user.id, item)
                purchased_apps.append(item.app)

            for item in cart.items:
                await self.cart_repo.session.delete(item)

            await self.cart_repo.write_off_funds_and_commit(user, total_price)

        except Exception as e:
            await self.cart_repo.session.rollback()
            logger.error(
                "\nAn error occurred during transaction:\n", exc_info=True
            )
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error occurred during transaction: {e}."
                "Please contact the developer",
            )
        
        await self.redis.delete(f"cart_cache:{user.id}")
        
        return purchased_apps

    async def remove_app_from_cart(
        self, 
        app_id: UUID, user_id: UUID
    ) -> None:
        await self.app_service.get_app(app_id)

        user_cart = await self.get_or_create_cart(user_id)
        cart_item = await self.get_cart_item(user_cart.id, app_id)

        if cart_item is None:
            raise app_not_in_cart_exception

        await self.redis.delete(f"cart_cache:{user_id}")

        user_cart.items.remove(cart_item)
        
        await self.cart_repo.remove_app_from_cart(cart_item)

    async def clear_cart(
        self, user_id: UUID
    ) -> None:
        cart = await self.get_or_create_cart(user_id)

        if not cart.items:
            raise empty_cart_exception

        await self.redis.delete(f"cart_cache:{user_id}")

        await self.cart_repo.clear_cart(cart)
