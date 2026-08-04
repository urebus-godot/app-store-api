from uuid import UUID
from typing import Optional
from collections import defaultdict
from decimal import Decimal

from redis.asyncio import Redis
from fastapi import BackgroundTasks

from app.uow.orm import UnitOfWork
from app.utils.email_send import send_email

from app.utils.time import get_time_string
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    insufficient_funds_exception,
    app_purchased_exception,
    app_in_cart_exception,
    app_published_exception,
    empty_cart_exception,
    app_not_in_cart_exception,
    app_not_found_exception
)
from app.repo.purchase_repo import PurchaseRepository

from app.service.app_service import AppService
from app.service.user_service import UserService

from app.models.app import AppDB
from app.models.purchase import PurchaseDB, CartItem, CartDB
from app.schemas.purchase import CartResponse


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

    async def get_or_create_cart(
        self, user_id: UUID, uow: UnitOfWork
    ) -> CartDB:
        logger.info("Start creating or getting cart")
        cart = await uow.purchase_repo.get_cart(user_id)
        logger.info(f"Get cart: {cart}")

        if cart is None:
            async with uow:
                cart = await uow.purchase_repo.create_cart(user_id)
                logger.info(f"Created cart in the db: {cart}")
                await uow.commit()

        return cart

    async def get_cart_for_user(
        self, user_id: UUID, uow: UnitOfWork
    ) -> CartResponse:
        """Returns user's cart or creates it and writes to the cache"""
        cached_cart = await self.redis.get(f"cart_cache:{user_id}")

        if cached_cart is not None:
            cart = CartResponse.model_validate_json(cached_cart)
            logger.info(f"Found cart in the cache: {cart}")
            return cart

        async with uow:
            cart = await uow.purchase_repo.get_cart(user_id)

            if cart is None:
                cart = await uow.purchase_repo.create_cart(user_id)
                await uow.commit()

            total_price = sum([item.app.price for item in cart.items])
            cart = CartResponse.model_validate(cart)
            cart.total_price = total_price

            logger.info(f"User's cart: {cart}")
            await self.redis.set(
                name=f"cart_cache:{user_id}",
                value=cart.model_dump_json(),
                ex=settings.CACHE_TTL_SECONDS,
            )
            logger.info("Added cart to the cache")

        return cart

    async def get_purchase_history(
        self, user_id: UUID, skip: int, limit: int
    ) -> list[PurchaseDB]:
        purchases = await self.purchase_repo.get_purchases(
            user_id, skip, limit
        )
        return purchases

    async def add_app_to_cart(
        self, app_id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> CartItem:
        async with uow:
            user_cart = await self.get_or_create_cart(user_id, uow)
            app = await self.app_service.get_app(app_id)

            purchased = await uow.purchase_repo.get_purchase(app_id, user_id)
            already_added = await uow.purchase_repo.get_cart_item(
                user_cart.id, app_id
                )

            if purchased:
                raise app_purchased_exception

            if already_added:
                raise app_in_cart_exception

            if app.publisher_id == user_id:
                raise app_published_exception

            await self.redis.delete(f"cart_cache:{user_id}")

            cart_item = await uow.purchase_repo.add_app_to_cart(
                user_cart, app_id
            )
            await uow.commit()

        return cart_item

    async def purchase_apps_in_cart(
        self, 
        user_id: UUID,
        user_email: Optional[str],
        bg_tasks: BackgroundTasks,
        uow: UnitOfWork
    ) -> list[AppDB]:
        async with uow:
            logger.info("Start purchasing apps")
            
            user = await uow.user_repo.get_user_by_id(
                user_id, for_update=True
                )
            cart = await uow.purchase_repo.get_cart(user.id)
            
            if cart is None or not cart.items:
                raise empty_cart_exception

            purchased_apps = []
            actual_total_price = 0
            publisher_earnings = defaultdict(Decimal)

            for item in cart.items:
                purchased = await uow.purchase_repo.get_purchase(
                    item.app_id, user.id
                    )
                if purchased:
                    logger.info(
                        f"App {item.app_id} is already purchased, skipping"
                        )
                    continue
                
                purchased_apps.append(item)
                actual_total_price += item.app.price
                
                # Копим деньги для издателей
                pub_id = item.app.publisher_id
                publisher_earnings[pub_id] += item.app.price

            # Если все игры из корзины уже куплены
            if not purchased_apps:
                await self.delete_cart(user_id, uow)
                await self.redis.delete(f"cart_cache:{user.id}")
                return []

            # 3. Проверяем баланс по актуальной стоимости
            if user.balance < actual_total_price:
                raise insufficient_funds_exception

            # 4. Проводим списания и начисления внутри БД
            user.balance -= actual_total_price
            
            for item in purchased_apps:
                await uow.purchase_repo.add_purchase(user.id, item)
                item.app.times_purchased += 1

            for pub_id, earnings in publisher_earnings.items():
                publisher = await uow.user_repo.get_user_by_id(
                    pub_id, for_update=True
                    )
                publisher.balance += earnings

            # 5. Удаляем корзину и кэш
            await self.delete_cart(user_id, uow)
            await self.redis.delete(f"cart_cache:{user.id}")
            
            # 6. Фиксируем транзакцию в БД
            await uow.commit()
            logger.info("Transaction has ended successfully")

            # 7. Только ПОСЛЕ успешного коммита планируем отправку Email
            if user.email is not None:
                app_names = ", ".join(
                    item.app.title for item in purchased_apps
                    )
                email_body = settings.RECEIPT_TEMPLATE % (
                    actual_total_price, app_names, get_time_string()
                )
                bg_tasks.add_task(
                    send_email, 
                    [str(user.email)], 
                    "Apps have been purchased", 
                    email_body
                )

            return [item.app for item in purchased_apps]
    
    async def remove_item_from_cart(
        self, app_id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            app = await uow.app_repo.get_app(app_id)

            if app is None:
                raise app_not_found_exception

            user_cart = await uow.purchase_repo.get_cart(user_id)
            cart_item = await uow.purchase_repo.get_cart_item(
                user_cart.id, app_id
                )

            if cart_item is None:
                raise app_not_in_cart_exception

            await self.redis.delete(f"cart_cache:{user_id}")
            await uow.purchase_repo.remove_item_from_cart(cart_item)
            await uow.commit()

    async def delete_cart(
        self, user_id: UUID, uow: UnitOfWork
    ) -> None:
        await uow.purchase_repo.delete_cart(user_id)

    async def delete_cart_by_user(
        self, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            cart = await uow.purchase_repo.get_cart(user_id)

            if cart is None:
                raise empty_cart_exception
            
            await self.redis.delete(f"cart_cache:{user_id}")
            await uow.purchase_repo.delete_cart(cart)
            await uow.commit()