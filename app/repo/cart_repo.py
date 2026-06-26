from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.user import UserDB
from app.models.app import AppDB
from app.models.app_purchase import Cart, Purchase, CartItem

from app.repo.app_repo import AppRepository

class AbstractCartRepository(ABC):
    @abstractmethod
    async def get_or_create_cart(user_id: UUID) -> Cart:
        pass

    @abstractmethod
    async def add_app_to_cart(
        self, user: UserDB,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def purchase_apps_in_cart(
        self, user: UserDB, total_cost: Decimal
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def remove_app_from_cart(
        self, id: UUID, user: UserDB
    ):
        pass


class CartRepository(AbstractCartRepository):
    def __init__(
        self, session: AsyncSession, app_repo: AppRepository
    ):
        self.session = session
        self.app_repo = app_repo

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        cart = (await self.session.exec(
            select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
        )).one_or_none()
        if cart is None:
            cart = Cart(user_id=user_id)

            self.session.add(cart)
            await self.session.commit()
            #self.session.refresh(cart)

        return cart

    async def add_app_to_cart(
        self, user: UserDB,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> dict[str, str]:
        if app is None:
            app = await self.app_repo.get_app(id)

        cart_item = CartItem(cart_id=user.cart.id, app_id=app.id)
  
        self.session.add(cart_item)
        await self.session.commit()
        await self.session.refresh(cart_item)

        return {"message": "App has been added to the cart"}

    async def purchase_apps_in_cart(
        self, user: UserDB, total_cost: Decimal
    ) -> dict[str, str]:
        user.purchased_apps = user.purchased_apps + user.cart
        user.cart = []
        user.balance -= total_cost

        self.session.add(user)
        await self.session.refresh(user)

        return {"message": "Apps has been purchased"}

    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ):
        item = (await self.session.exec(
            select(CartItem).where(
                CartItem.cart_id == cart_id, CartItem.app_id == app_id
                )
        )).first()
        return item

    async def add_purchase(
        self, user_id: UUID, item: CartItem
    ):
        purchase = Purchase(
            user_id=user_id, app_id=item.app_id, price=item.price
            )
        self.session.add(purchase)

    async def remove_app_from_cart(
        self, user: UserDB, app: AppDB
    ):
        cart = user.cart
        cart_item = await self.get_cart_item(cart.id, app.id)

        self.session.delete(cart_item)
        await self.session.commit()

        return {"message": "App has bee removed from the cart"}