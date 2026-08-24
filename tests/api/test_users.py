from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest

from app.models.user import UserDB, UserRole


class TestUsers:
    async def test_get_current_user(self, auth_client: AsyncClient):
        response = await auth_client.get("/api/v1/users/me")
        data = response.json()
        assert response.status_code == 200
        assert "password" not in data
        assert data["username"] == "testUser"

    async def test_get_user(
        self, 
        auth_client: AsyncClient,
        test_user_2: UserDB
    ):
        response = await auth_client.get(
            "/api/v1/users/anotherUser"
            )
        data = response.json()
        assert response.status_code == 200
        assert "password" not in data
        assert data["username"] == "anotherUser"

    async def test_get_users(
        self, 
        auth_client: AsyncClient,
        db_session: AsyncSession
    ):
        users = [
            UserDB(
                username="user1",
                hashed_password="1234567890"
            ),
            UserDB(
                username="user2",
                hashed_password="1234567890"
            ),
        ]
        db_session.add_all(users)
        await db_session.flush()

        response = await auth_client.get(
            "/api/v1/users"
            )
        data = response.json()
        assert response.status_code == 200
        assert len(data) == 3
        assert "username" in data[0]

    async def test_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users", 
            json={"username": "myuser", "password": "12345678"}
        )
        assert response.status_code == 201
        assert response.json()["username"] is not None

    @pytest.mark.parametrize(
        argnames=["update_data", "expected_data", "expected_status_code"],
        argvalues=[
            [{"username": "test1"}, {"username": "test1"}, 200],
            [{"balance": "10000"}, {"balance": "0"}, 200],
            [{"name": "serega"}, {"username": "testUser"}, 200],
            [{"username": " user"}, {}, 422],
            [{"password": "          "}, {}, 422],
        ],
    )
    async def test_update_user(
        self,
        auth_client: AsyncClient,
        update_data: dict,
        expected_data: dict,
        expected_status_code: int,
    ):
        response = await auth_client.patch(
            "/api/v1/users/me", json=update_data
        )
        data = response.json()

        assert response.status_code == expected_status_code
        for key in expected_data.keys():
            assert data[key] == expected_data[key]

    async def test_delete_current_user(
        self,
        auth_client: AsyncClient,
        test_user: UserDB,
        fake_redis: FakeRedis
    ):
        delete_response = await auth_client.delete("/api/v1/users/me")
        assert delete_response.status_code == 204
        assert not await fake_redis.exists(f"user_tokens:{test_user.id}")

        get_response = await auth_client.get(f"/api/v1/users/{test_user.id}")
        assert get_response.status_code == 404

    async def test_set_admin_role(
        self, 
        auth_client: AsyncClient,
        db_session: AsyncSession
    ):
        admin_role_response = await auth_client.post(
            "/api/v1/users/me/roles/admin",
            params={"password": "adminpass"}
        )
        assert admin_role_response.status_code == 200
        return
        get_user_response = await auth_client.get(
            "/api/v1/users/me"
        )
        data = get_user_response.json()
        assert UserRole.ADMIN.value in data["roles"]

    async def test_set_admin_role_wrong_password(
        self, 
        auth_client: AsyncClient,
        test_user: UserDB,
    ):
        admin_role_response = await auth_client.post(
            "/api/v1/users/me/roles/admin",
            params={"password": "wrongpass"}
        )
        assert admin_role_response.status_code == 401


class TestUserFiles:
    pass