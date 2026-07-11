from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest_asyncio

from app.models.user import UserDB
from app.models.app import AppDB
from app.models.purchase import Cart, CartItem


@pytest_asyncio.fixture
async def test_cart(
    test_user: UserDB,
    db_session: AsyncSession,
    test_app_2: AppDB,
    test_app_2_paid: AppDB,
):
    cart = Cart(user_id=test_user.id)
    item_1 = CartItem(cart_id=cart.id, app_id=test_app_2.id)
    item_2 = CartItem(cart_id=cart.id, app_id=test_app_2_paid.id)

    db_session.add(cart)
    db_session.add_all([item_1, item_2])
    await db_session.commit()

    return cart


class TestCart:
    async def test_add_app_to_cart(
        self,
        auth_client: AsyncClient,
        test_app_2_paid: AppDB,
        test_user: UserDB,
    ):
        add_response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}/{test_app_2_paid.id}"
        )
        data = add_response.json()

        assert add_response.status_code == 201
        assert data["app_id"] == str(test_app_2_paid.id)

        get_cart_response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}"
        )
        data = get_cart_response.json()

        assert get_cart_response.status_code == 200
        assert data["total_price"] == "1000"

    async def test_add_app_to_cart_not_exists(
        self,
        auth_client: AsyncClient,
        test_app_2_paid: AppDB,
        test_user: UserDB,
    ):
        response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}/097c51bc-3c31-4cdf-b726-a4b1df084d8e"
        )
        assert response.status_code == 404

    async def test_add_own_app_to_cart(
        self, auth_client: AsyncClient, test_app: AppDB, test_user: UserDB
    ):
        response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}/{test_app.id}"
        )

        assert response.status_code == 400

    async def test_remove_app_from_cart(
        self,
        auth_client: AsyncClient,
        test_app_2_paid: AppDB,
        test_user: UserDB,
        test_cart: Cart,
    ):
        remove_response = await auth_client.delete(
            f"/api/v1/carts/{test_user.id}/{test_app_2_paid.id}"
        )

        assert remove_response.status_code == 204

        get_cart_response = await auth_client.post(
            f"/api/v1/carts/{test_user.id}"
        )
        data = get_cart_response.json()

        assert data["total_price"] == "0"
        assert len(data["items"]) == 1

    async def test_get_cart(
        self,
        auth_client: AsyncClient,
        test_user: UserDB,
    ):
        response = await auth_client.post(f"/api/v1/carts/{test_user.id}")
        data = response.json()

        assert response.status_code == 200
        assert data["total_price"] == "0"

    async def test_purchase_apps_in_cart(
        self, auth_client: AsyncClient, test_user: UserDB, test_cart: Cart
    ):
        test_user.balance = 10000

        checkout_response = await auth_client.post("/api/v1/carts/checkout")
        assert checkout_response.status_code == 200
        assert len(checkout_response.json()) == 2

        get_apps_response = await auth_client.get("/api/v1/apps/purchased/me")
        assert get_apps_response.status_code == 200
        assert len(get_apps_response.json()) == 2

        get_user_response = await auth_client.get("/api/v1/users/me")
        data = get_user_response.json()
        assert data["balance"] == "9000"

    async def test_purchase_apps_in_cart_unsufficient_funds(
        self,
        auth_client: AsyncClient,
        test_user: UserDB,
        test_cart: Cart,
        db_session: AsyncSession,
    ):
        checkout_response = await auth_client.post("/api/v1/carts/checkout")
        assert checkout_response.status_code == 400
