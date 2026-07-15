import pytest
from httpx import AsyncClient

from app.models.user import UserDB


class TestFinance:
    @pytest.mark.parametrize(
        argnames=["amount", "expected_balance", "expected_status_code"],
        argvalues=[
            [1_000, "1000", 200],
            [1_000_000_000, "1000000000", 200],
            [0.00001, "0.00001", 200],
            [0, "0", 422],
            [-1_000, "0", 422],
        ],
    )
    async def test_top_up_balance(
        self,
        auth_client: AsyncClient,
        amount: float,
        expected_balance: str,
        expected_status_code: int,
    ):
        response = await auth_client.post(
            "/api/v1/transfers/balance", 
            json={"amount": amount}
        )
        assert response.status_code == expected_status_code
        if response.status_code == 200:
            assert response.json()["new_balance"] == expected_balance

    @pytest.mark.parametrize(
        argnames=["amount", "expected_balance", "expected_status_code"],
        argvalues=[
            [1_000, "9000", 200],
            [1_000_000_000, "10000", 400],
            [0, "0", 422],
            [-1_000, "0", 422],
        ],
    )
    async def test_withdraw_funds_to_card(
        self,
        auth_client: AsyncClient,
        test_user: UserDB,
        amount: float,
        expected_balance: str,
        expected_status_code: int
    ):
        test_user.balance = 10000
        response = await auth_client.post(
            "/api/v1/transfers/withdrawal", 
            json={"amount": amount}
        )
        assert response.status_code == expected_status_code
        if response.status_code == 200:
            assert response.json()["new_balance"] == expected_balance

    async def test_get_transfer_history(
        self,
        auth_client: AsyncClient
    ):
        response = await auth_client.get(
            "/api/v1/transfers/history"
        )
        assert response.status_code == 200