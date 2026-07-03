from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.core.logging import logger

from app.models.user import UserDB
from app.models.app import AppDB
from app.models.app_purchase import Cart, Purchase, CartItem

from app.repo.app_repo import AppRepository

class AbstractCartRepository(ABC):
    @abstractmethod
    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        pass

    @abstractmethod
    async def get_purchase(
        self, app_id: UUID, user_id: UUID
    ) -> Optional[Purchase]:
        pass

    @abstractmethod
    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ) -> Optional[CartItem]:
        pass

    @abstractmethod
    async def add_app_to_cart(
        self, user: Cart,
        app_id: UUID
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def purchase_apps_in_cart(
        self, user: UserDB, total_cost: Decimal
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def write_off_funds_and_commit(
        self, user: UserDB, total_price: Decimal
    ) -> None:
        pass

    @abstractmethod
    async def remove_app_from_cart(
        self, id: UUID, user: UserDB
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def clear_cart(self, cart: Cart) -> dict[str, str]:
        pass


class CartRepository(AbstractCartRepository):
    def __init__(
        self, session: AsyncSession, app_repo: AppRepository
    ):
        self.session = session
        self.app_repo = app_repo
        self.load_attrs = (
            selectinload(Cart.items).selectinload(CartItem.app), 
            selectinload(Cart.user)
            )

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        cart = (await self.session.exec(
            select(Cart).where(
                Cart.user_id == user_id
                ).options(*self.load_attrs)
        )).one_or_none()

        if cart is None:
            cart = Cart(user_id=user_id)

            self.session.add(cart)
           
            cart = (await self.session.exec(
                select(Cart).where(
                    Cart.user_id == user_id
                    ).options(*self.load_attrs)
            )).one()

        return cart
    
    async def get_purchase(
        self, app_id: UUID, user_id: UUID
    ) -> Optional[Purchase]:
        purchase = (await self.session.exec(
            select(Purchase).where(
                Purchase.app_id == app_id,
                Purchase.user_id == user_id
            )
        )).first()
        return purchase

    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ) -> Optional[CartItem]:
        item = (await self.session.exec(
            select(CartItem).where(
                CartItem.cart_id == cart_id, 
                CartItem.app_id == app_id
                ).options(selectinload(CartItem.app), selectinload(CartItem.cart))
        )).first()
        return item

    async def add_app_to_cart(
        self, cart: Cart,
        app_id: UUID,
    ) -> dict[str, str]:
        cart_item = CartItem(cart_id=cart.id, app_id=app_id)
  
        self.session.add(cart_item)
        await self.session.commit()

        return {"message": "App has been added"}

    async def purchase_apps_in_cart(
        self, user: UserDB, total_cost: Decimal
    ) -> dict[str, str]:
        user.purchased_apps = user.purchased_apps + user.cart
        user.cart = []
        user.balance -= total_cost

        self.session.add(user)
        #await self.session.refresh(user)

        return {"message": "Apps have been purchased"}

    async def write_off_funds_and_commit(
        self, user: UserDB, total_price: Decimal
    ) -> None:
        user.balance -= total_price
        self.session.add(user)
        await self.session.commit()

    async def add_purchase(
        self, user_id: UUID, item: CartItem
    ) -> None:
        purchase = Purchase(
            user_id=user_id, app_id=item.app_id, price=item.app.price
            )
        self.session.add(purchase)

    async def remove_app_from_cart(
        self, cart: Cart, item: CartItem
    ) -> dict[str, str]:
        self.session.delete(item)
        await self.session.commit()

        return {"message": "App has been removed"}

    async def clear_cart(self, cart: Cart) -> dict[str, str]:
        await self.session.delete(cart)
        await self.session.commit()

        return {"message": "Cart has been cleared"}