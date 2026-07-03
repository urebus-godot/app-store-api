from httpx import AsyncClient

from testing.conftest import test_user_data

async def test_get_current_user(
    client: AsyncClient, auth_header: dict[str, str]
):
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_header
        )
    data = response.json()

    assert response.status_code == 200
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]