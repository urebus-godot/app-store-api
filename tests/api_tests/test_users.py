from pathlib import Path
from io import BufferedReader
import os
import shutil

from httpx import AsyncClient
from fakeredis.aioredis import FakeRedis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest

from app.models.user import UserDB
from app.models.file import UserProfilePicture

@pytest.fixture(scope="function")
def test_image(test_user: UserDB):
    file_path = Path("tests/files/test_image.PNG")

    with open(file_path, "rb") as file:
        yield file

        uploaded_file_path = Path(
            f"media/static/profile_pictures/{test_user.id}.PNG"
            )

        if uploaded_file_path.exists():
            os.remove(uploaded_file_path)


@pytest.fixture(scope="function")
async def test_profile_picture(
    db_session: AsyncSession,
    test_user: UserDB,
    test_image: BufferedReader
    ):
    profile_picture = UserProfilePicture(
        user_id=test_user.id,
        extension=".PNG"
    )
    db_session.add(profile_picture)
    await db_session.flush()

    file_dst_path = Path(f"media/static/profile_pictures/{test_user.id}.PNG")
    file_dst_path.touch()

    with open(file_dst_path, "wb") as dst_file:
        shutil.copyfileobj(test_image, dst_file, 1024 * 1024)

    yield profile_picture

    if file_dst_path.exists():
        os.remove(file_dst_path)


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


class TestUserFiles:
    async def test_upload_profile_picture(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        test_user: UserDB,
        test_image: BufferedReader
    ):
        response = await auth_client.post(
            "/api/v1/users/me/profile_picture",
            files={
                "file": (
                    "test_image.PNG", 
                    test_image.read(), 
                    "image/png"
                    )
                }
        )
        data = response.json()

        profile_picture = (await db_session.exec(
            select(UserProfilePicture).where(
                UserProfilePicture.user_id == test_user.id,
                UserProfilePicture.extension == ".PNG"
            )
        )).one_or_none()

        assert response.status_code == 201
        assert data["extension"] == ".PNG"
        assert data["user_id"] == str(test_user.id)
        assert Path(
            f"media/static/profile_pictures/{test_user.id}.PNG"
            ).exists()
        assert profile_picture is not None

    async def test_upload_profile_picture_wrong_ext(
        self,
        auth_client: AsyncClient
    ):
        file_path = Path("tests/files/test_app_archive.zip")

        with open(file_path, "rb") as file:
            response = await auth_client.post(
                "/api/v1/users/me/profile_picture",
                files={
                    "file": (
                        "test_image.zip", 
                        file.read(), 
                        "image/png"
                        )
                    }
            )
            assert response.status_code == 415

    async def test_remove_profile_picture(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        test_user: UserDB,
        test_profile_picture: Path
    ):
        response = await auth_client.delete(
            "/api/v1/users/me/profile_picture"
        )
        profile_picture = (await db_session.exec(
            select(UserProfilePicture).where(
                UserProfilePicture.user_id == test_user.id
            )
        )).one_or_none()

        assert response.status_code == 204
        assert not Path(
            f"media/static/profile_pictures/{test_user.id}.PNG"
            ).exists()
        assert profile_picture is None

    async def test_remove_profile_picture_not_exists(
        self,
        auth_client: AsyncClient
    ):
        response = await auth_client.delete(
            "/api/v1/users/me/profile_picture"
        )
        assert response.status_code == 400