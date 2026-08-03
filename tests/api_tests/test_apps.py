from pathlib import Path
from io import BufferedReader
from uuid import UUID
import shutil
import os

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from httpx import AsyncClient
from fastapi.exceptions import ResponseValidationError
import pytest

from app.models.app import AppDB
from app.models.user import UserDB
from app.models.file import AppArchive, AppCover, AppThumbnail
from app.models.purchase import PurchaseDB
from app.models.review import ReviewDB

from app.core.config import settings

@pytest.fixture(scope="function")
def test_archive(test_app: AppDB):
    file_path = Path("tests/files/test_app_archive.zip")

    with open(file_path, "rb") as file:
        yield file

        uploaded_file_path = Path(
            f"media/app_archives/{test_app.id}.zip"
            )

        if uploaded_file_path.exists():
            os.remove(uploaded_file_path)

@pytest.fixture(scope="function")
async def test_app_archive(
    db_session: AsyncSession,
    test_app: AppDB,
    test_archive: BufferedReader
    ):
    app_archive = AppArchive(
        app_id=test_app.id,
        filename="test_app_archive.zip"
    )
    db_session.add(app_archive)
    await db_session.flush()

    file_dst_path = Path(f"media/app_archives/{test_app.id}.zip")
    file_dst_path.touch()

    with open(file_dst_path, "wb") as dst_file:
        shutil.copyfileobj(test_archive, dst_file, 1024 * 1024)

    yield app_archive

    if file_dst_path.exists():
        os.remove(file_dst_path)


@pytest.fixture(scope="function")
def test_cover():
    file_path = Path("tests/files/test_app_cover.PNG")

    with open(file_path, "rb") as file:
        yield file

        uploaded_file_path = Path(
            "media/static/applications/covers/abf890b2-459e-4977-92b4-fa628fa10e2d.PNG"
            )

        if uploaded_file_path.exists():
            os.remove(uploaded_file_path)

@pytest.fixture(scope="function")
async def test_app_cover(
    db_session: AsyncSession,
    test_app: AppDB,
    test_cover: BufferedReader
    ):
    app_cover = AppCover(
        id=UUID("abf890b2-459e-4977-92b4-fa628fa10e2d"),
        app_id=test_app.id,
        extension=".PNG"
    )
    db_session.add(app_cover)
    await db_session.flush()

    file_dst_path = Path(
        "media/static/applications/covers/abf890b2-459e-4977-92b4-fa628fa10e2d.PNG"
        )
    file_dst_path.touch()

    with open(file_dst_path, "wb") as dst_file:
        shutil.copyfileobj(test_cover, dst_file, 1024 * 1024)

    yield app_cover

    if file_dst_path.exists():
        os.remove(file_dst_path)


@pytest.fixture(scope="function")
def test_thumbnail(test_app: AppDB):
    file_path = Path("tests/files/test_image.PNG")

    with open(file_path, "rb") as file:
        yield file

        uploaded_file_path = Path(
            f"media/static/applications/thumbnails/{test_app.id}.PNG"
            )

        if uploaded_file_path.exists():
            os.remove(uploaded_file_path)

@pytest.fixture(scope="function")
async def test_app_thumbnail(
    db_session: AsyncSession,
    test_app: AppDB,
    test_thumbnail: BufferedReader
    ):
    app_thumbnail = AppThumbnail(
        id=UUID("abf890b2-459e-4977-92b4-fa628fa10e2d"),
        app_id=test_app.id,
        extension=".PNG"
    )
    db_session.add(app_thumbnail)
    await db_session.flush()

    file_dst_path = Path(
        f"media/static/applications/thumbnails/{test_app.id}.PNG"
        )
    file_dst_path.touch()

    with open(file_dst_path, "wb") as dst_file:
        shutil.copyfileobj(test_thumbnail, dst_file, 1024 * 1024)

    yield app_thumbnail

    if file_dst_path.exists():
        os.remove(file_dst_path)


class TestApps:
    async def test_create_app(self, publisher_client: AsyncClient):
        response = await publisher_client.post(
            "/api/v1/apps", json={"title": "gta 6", "price": 500}
        )
        data = response.json()

        assert response.status_code == 201
        assert data["price"] == "500"

    async def test_create_app_not_publisher(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/v1/apps", json={"title": "gta 6", "price": 500}
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        argnames=["update_data", "expected_data", "expected_status_code"],
        argvalues=[
            [{"title": "Code"}, {"title": "Code"}, 200],
            [{"title": "   "}, {}, 422],
            [{"price": 600}, {"price": "600"}, 200],
            [{"price": "money"}, {}, 422],
        ],
    )
    async def test_update_app(
        self,
        auth_client: AsyncClient,
        test_app: AppDB,
        update_data: dict,
        expected_data: dict,
        expected_status_code: int,
    ):
        try:
            response = await auth_client.patch(
                f"/api/v1/apps/{test_app.id}", json=update_data
            )
            data = response.json()

            assert response.status_code == expected_status_code
            for key in expected_data.keys():
                assert data[key] == expected_data[key]
        except ResponseValidationError:
            pass

    async def test_delete_app(
        self, publisher_client: AsyncClient, test_app: AppDB
    ):
        delete_response = await publisher_client.delete(
            f"/api/v1/apps/{test_app.id}"
        )
        assert delete_response.status_code == 204

        get_response = await publisher_client.get(
            f"/api/v1/apps/{test_app.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_app_no_rights(
        self, publisher_client: AsyncClient, test_app_2: AppDB
    ):
        delete_response = await publisher_client.delete(
            f"/api/v1/apps/{test_app_2.id}"
        )
        assert delete_response.status_code == 403

    async def test_get_app(self, client: AsyncClient, test_app_2: AppDB):
        response = await client.get(f"/api/v1/apps/{test_app_2.id}")
        data = response.json()

        assert response.status_code == 200
        assert "genre" not in data

    async def test_get_game(self, client: AsyncClient, test_game: AppDB):
        response = await client.get(f"/api/v1/apps/{test_game.id}")
        data = response.json()

        assert response.status_code == 200
        assert "genre" in data

    async def test_get_private_app(
        self, client: AsyncClient, test_app_private: AppDB
    ):
        response = await client.get(f"/api/v1/apps/{test_app_private.id}")
        assert response.status_code == 404

    async def test_get_apps(
        self, 
        client: AsyncClient, 
        test_apps: list[AppDB]
    ):
        query = {"search_query": "KEY NEWKEY"}
        response = await client.get("/api/v1/apps", params=query)
        assert response.status_code == 200
        assert len(response.json()) == len(test_apps) - 1


class TestAppFiles:
    async def test_upload_app_archive(
        self, 
        publisher_client: AsyncClient, 
        db_session: AsyncSession,
        test_app: AppDB,
        test_archive: BufferedReader
    ):
        response = await publisher_client.post(
            f"/api/v1/apps/{test_app.id}/files/archive",
            files={
                "file": (
                    "test_app_archive.zip", 
                    test_archive, 
                    "application/zip" 
                )
            }
        )
        data = response.json()
        app_archive = (await db_session.exec(
            select(AppArchive).where(
                AppArchive.app_id == test_app.id,
                AppArchive.filename == "test_app_archive.zip"
            )
        )).one_or_none()

        assert response.status_code == 201
        assert data["filename"] == "test_app_archive.zip"
        assert data["app_id"] == str(test_app.id)
        assert Path(
            f"media/app_archives/{test_app.id}.zip"
            ).exists()
        assert app_archive is not None

    async def test_upload_app_archive_wrong_ext(
        self, 
        publisher_client: AsyncClient, 
        test_app: AppDB
    ):
        file_path = Path("tests/files/test_image.PNG")

        with open(file_path, "rb") as file:
            response = await publisher_client.post(
                f"/api/v1/apps/{test_app.id}/files/archive",
                files={
                    "file": (
                        "test_app_archive.PNG", 
                        file, 
                        "application/zip" 
                    )
                }
            )
            assert response.status_code == 415

    async def test_download_app_archive(
        self,
        publisher_client: AsyncClient,
        test_app_archive: AppArchive,
        test_app: AppDB
    ):
        
        response = await publisher_client.post(
            f"/api/v1/apps/{test_app.id}/download"
        )
        assert response.status_code == 200

    async def test_download_app_archive_not_purchased(
        self,
        auth_client_2: AsyncClient,
        test_user_2: UserDB,
        test_app_archive: AppArchive,
        test_app: AppDB
    ):
        response = await auth_client_2.post(
            f"/api/v1/apps/{test_app.id}/download"
        )
        assert response.status_code == 400

    async def test_upload_app_cover(
        self, 
        publisher_client: AsyncClient, 
        db_session: AsyncSession,
        test_app: AppDB,
        test_cover: BufferedReader
    ):
        try:
            response = await publisher_client.post(
                f"/api/v1/apps/{test_app.id}/files/covers",
                files={
                    "file": (
                        "test_app_cover.PNG", 
                        test_cover, 
                        "application/png" 
                    )
                }
            )
            data = response.json()
            app_cover = (await db_session.exec(
                select(AppCover).where(
                    AppCover.app_id == test_app.id,
                    AppCover.extension == ".PNG"
                )
            )).one_or_none()
            app_cover_path = Path(
                f"media/static/applications/covers/{app_cover.id}.PNG"
                )

            assert response.status_code == 201
            assert data["extension"] == ".PNG"
            assert app_cover is not None
            assert app_cover_path.exists()
        finally:
            if app_cover_path.exists():
                os.remove(app_cover_path)

    async def test_remove_app_cover(
        self, 
        publisher_client: AsyncClient, 
        db_session: AsyncSession,
        test_app: AppDB,
        test_app_cover: BufferedReader
    ):
        cover_id = await db_session.exec(
            select(AppCover.id).where(
                AppCover.app_id == test_app.id
            )
        )
        response = await publisher_client.delete(
            f"/api/v1/apps/files/covers/{test_app_cover.id}"
        )
        app_cover = (await db_session.exec(
            select(AppCover).where(
                AppCover.app_id == test_app.id
            )
        )).one_or_none()

        assert response.status_code == 204
        assert not (settings.APP_COVER_PATH / f"{cover_id}.PNG").exists()
        assert app_cover is None

    async def test_remove_app_cover_not_exists(
        self, 
        publisher_client: AsyncClient, 
        test_app: AppDB
    ):
        response = await publisher_client.delete(
            "/api/v1/apps/files/covers/abf890b2-459e-4977-92b4-fa628fa10e2d"
        )
        assert response.status_code == 404

    async def test_upload_app_thumbnail(
        self,
        db_session: AsyncSession,
        publisher_client: AsyncClient, 
        test_app: AppDB,
        test_thumbnail: BufferedReader
    ):
        response = await publisher_client.post(
            f"/api/v1/apps/{test_app.id}/files/thumbnail",
            files={
                "file": (
                    "test_app_thumbnail.PNG",
                    test_thumbnail,
                    "image/png"
                )
            }
        )
        data = response.json()

        assert response.status_code == 201
        app_thumbnail = (await db_session.exec(
            select(AppThumbnail).where(
                AppThumbnail.app_id == test_app.id,
                AppThumbnail.extension == ".PNG"
            )
        )).one_or_none()

        assert response.status_code == 201
        assert data["extension"] == ".PNG"
        assert app_thumbnail is not None
        assert (settings.APP_THUMBNAIL_PATH / f"{test_app.id}.PNG").exists()