from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload


from app.models.user import UserDB
from app.models.purchase import Cart, PurchaseDB, CartItem


class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.load_attrs = (
            selectinload(Cart.items).selectinload(CartItem.app),
            selectinload(Cart.user),
        )

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        cart = (
            await self.session.exec(
                select(Cart)
                .where(Cart.user_id == user_id)
                .options(*self.load_attrs)
            )
        ).one_or_none()

        if cart is None:
            cart = Cart(user_id=user_id)

            self.session.add(cart)

            cart = (
                await self.session.exec(
                    select(Cart)
                    .where(Cart.user_id == user_id)
                    .options(*self.load_attrs)
                )
            ).one()

        return cart

    async def get_purchase(
        self, app_id: UUID, user_id: UUID
    ) -> Optional[PurchaseDB]:
        purchase = (
            await self.session.exec(
                select(PurchaseDB).where(
                    PurchaseDB.app_id == app_id, PurchaseDB.user_id == user_id
                )
            )
        ).first()
        return purchase

    async def get_cart_item(
        self, cart_id: UUID, app_id: UUID
    ) -> Optional[CartItem]:
        item = (
            await self.session.exec(
                select(CartItem)
                .where(CartItem.cart_id == cart_id, CartItem.app_id == app_id)
                .options(
                    selectinload(CartItem.app), selectinload(CartItem.cart)
                )
            )
        ).first()

        return item

    async def get_purchases(
        self, user_id: UUID, skip: int, limit: int
    ) -> list[PurchaseDB]:
        purchases = (
            await self.session.exec(
                select(PurchaseDB)
                .where(PurchaseDB.user_id == user_id)
                .order_by(desc(PurchaseDB.purchased_at))
                .offset(skip)
                .limit(limit)
            )
        ).all()

        return purchases

    async def add_app_to_cart(
        self,
        cart: Cart,
        app_id: UUID,
    ) -> CartItem:
        cart_item = CartItem(cart_id=cart.id, app_id=app_id)

        self.session.add(cart_item)
        await self.session.commit()

        return cart_item

    async def write_off_funds_and_commit(
        self, user: UserDB, total_price: Decimal
    ) -> None:
        user.balance -= total_price
        self.session.add(user)
        await self.session.commit()

    async def add_purchase(self, user_id: UUID, item: CartItem) -> None:
        purchase = PurchaseDB(
            user_id=user_id, app_id=item.app_id, price=item.app.price
        )
        self.session.add(purchase)

    async def remove_app_from_cart(self, item: CartItem) -> None:
        await self.session.delete(item)
        await self.session.commit()

    async def clear_cart(self, cart: Cart) -> None:
        await self.session.delete(cart)
        await self.session.commit()
