from unittest.mock import patch, Mock
import pytest

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

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
        db_session: AsyncSession,
        test_user: UserDB,
        amount: float,
        expected_balance: str,
        expected_status_code: int
    ):
        test_user.balance = 10000
        await db_session.flush()

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

    @patch("app.services.finance_service.AsyncClient.get")
    @pytest.mark.parametrize(
        argnames=["currency", "rate"],
        argvalues=[
            ["EUR", 0.011],
            ["USD", 0.013],
            ["GBP", 0.0095]
        ],
    )
    async def test_get_balance(
        self,
        mock_get,
        auth_client: AsyncClient, 
        currency: str,
        rate: float,
        test_user: UserDB,
        logger
        ):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
                "date": "2026-01-01",
                "base": "RUB",
                "quote": currency,
                "rate": rate
        }
        mock_get.return_value = mock_response
        test_user.balance = 1000
        response = await auth_client.get(
            "/api/v1/finance/me/balance",
            params={
                "currency": currency
                }
            )
        data = response.json()
        logger.info(f"\n\ndata: {data}\n\n")

        assert response.status_code == 200
        assert data["currency"] == currency
        assert float(data["balance"]) == round(test_user.balance * rate, 5)