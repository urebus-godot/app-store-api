from uuid import UUID
from typing import Optional

from redis.asyncio import Redis

from app.uow.unit_of_work import UnitOfWork
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    insufficient_funds_exception,
    app_purchased_exception,
    app_in_cart_exception,
    app_published_exception,
    empty_cart_exception,
    app_not_in_cart_exception,
    cart_not_found_exception
)
from app.repo.purchase_repo import PurchaseRepository
from app.service.app_service import AppService
from app.service.user_service import UserService
from app.models.app import AppDB
from app.models.purchase import PurchaseDB, CartItem, CartDB


class PurchaseService:
    def __init__(
        self,
        redis: Redis,
        app_service: AppService,
        user_service: UserService,
        purchase_repo: PurchaseRepository,
    ):
        self.redis = redis
        self.purchase_repo = purchase_repo
        self.app_service = app_service
        self.user_service = user_service

    async def get_or_create_cart(self, user_id: UUID):
        logger.info("Start creating or getting cart")
        cart = await self.purchase_repo.get_cart(user_id)
        logger.info(f"Fetched cart: {cart}")

        if cart is None:
            cart = await self.purchase_repo.create_cart(user_id)
            logger.info(f"Created cart in the db: {cart}")

            await self.redis.set(
                name=f"cart_cache:{user_id}",
                value=cart.model_dump_json(),
                ex=settings.CACHE_TTL_SECONDS,
            )
        logger.info("Added cart to the cache")

        return cart

    async def get_cart(self, user_id: UUID):
        cached_cart = await self.redis.get(f"cart_cache:{user_id}")

        if False and cached_cart is not None:
            cart = CartDB.model_validate_json(cached_cart)
            logger.info(f"Found cart in the cache: {cart}")
            return cart

        cart = await self.purchase_repo.get_cart(user_id)

        if cart is None:
            raise cart_not_found_exception
        logger.info(f"User's cart: {cart}")
        await self.redis.set(
            name=f"cart_cache:{user_id}",
            value=cart.model_dump_json(),
            ex=settings.CACHE_TTL_SECONDS,
        )
        logger.info("Added cart to the cache")

        return cart

    async def get_purchase(
        self, app_id: UUID, user_id: UUID
    ) -> Optional[PurchaseDB]:
        purchase = await self.purchase_repo.get_purchase(app_id, user_id)
        return purchase

    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ) -> Optional[CartItem]:
        item = await self.purchase_repo.get_cart_item(cart_id, app_id)
        return item

    async def get_purchase_history(
        self, user_id: UUID, skip: int, limit: int
    ) -> list[PurchaseDB]:
        purchases = await self.purchase_repo.get_purchases(
            user_id, skip, limit
        )
        return purchases

    async def add_app_to_cart(
        self, app_id: UUID, user_id: UUID
    ) -> CartItem:
        user_cart = await self.get_or_create_cart(user_id)
        app = await self.app_service.get_app(app_id)

        purchased = await self.get_purchase(app_id, user_id)
        already_added = await self.get_cart_item(user_cart.id, app_id)

        if purchased:
            raise app_purchased_exception

        if already_added:
            raise app_in_cart_exception

        if app.publisher_id == user_id:
            raise app_published_exception

        await self.redis.delete(f"cart_cache:{user_id}")

        cart_item = await self.purchase_repo.add_app_to_cart(
            user_cart, app_id
        )

        return cart_item

    async def purchase_apps_in_cart(
        self, user_id: UUID, uow: UnitOfWork
    ) -> list[AppDB]:
        async with uow:
            user = await self.user_service.get_user_by_id(user_id)

            logger.info("Start purchasing apps")
            cart = await self.get_or_create_cart(user.id)
            total_price = sum(item.app.price for item in cart.items)
            logger.info(
                f"Cart: {cart}\nItems: {cart.items}\nPrice: {total_price}"
                )

            if not cart.items:
                raise empty_cart_exception

            if user.balance < total_price:
                raise insufficient_funds_exception

            purchased_apps = []

            for item in cart.items:
                purchased = await self.get_purchase(item.app_id, user.id)
                if purchased:
                    logger.info("App is purchased, so skip it")
                    continue

                await self.purchase_repo.add_purchase(user.id, item)
                purchased_apps.append(item.app)
                logger.info("Added app to purchases")

                item.app.times_purchased += 1
                app_publisher = await self.user_service.get_user_by_id(
                    item.app.publisher_id
                )
                app_publisher.balance += item.app.price

            await self.delete_cart(user_id)
            logger.info("Deleted items in cart")
            logger.info(f"Items: {cart.items}")

            user.balance -= total_price
            await self.redis.delete(f"cart_cache:{user.id}")
            await uow.commit()

            logger.info("Transaction has ended successfully")

            return purchased_apps

    async def remove_item_from_cart(
        self, app_id: UUID, user_id: UUID, commit: bool
    ) -> None:
        await self.app_service.get_app(app_id)

        user_cart = await self.get_cart(user_id)
        cart_item = await self.get_cart_item(user_cart.id, app_id)

        if cart_item is None:
            raise app_not_in_cart_exception

        await self.redis.delete(f"cart_cache:{user_id}")
        await self.purchase_repo.remove_item_from_cart(cart_item, commit)

    async def delete_cart(self, user_id: UUID) -> None:
        cart = await self.get_or_create_cart(user_id)
        
        await self.redis.delete(f"cart_cache:{user_id}")
        await self.purchase_repo.delete_cart(cart)

