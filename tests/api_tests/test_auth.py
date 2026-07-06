from httpx import AsyncClient

from tests.conftest import test_user_data

class TestAuth:
    async def test_login(client: AsyncClient):
        response = await client.get(
            "/api/v1/users/login",
            )
        data = response.json()

        assert response.status_code == 200
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]