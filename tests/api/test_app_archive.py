from httpx import AsyncClient

from sqlmodel.ext.asyncio.session import AsyncSession

import pytest

from app.core.config import settings

from app.storage.minio_repo import MinioStorage

from app.models.app import AppDB


@pytest.fixture(scope="function")
async def upload_test_archive(
    minio_client: AsyncClient,
    object_storage: MinioStorage,
    test_app: AppDB, db_session: AsyncSession
):
    fake_archive_file = b"app data " * 100_000
    content_type = "application/zip"

    upload_url = await object_storage.generate_presigned_upload_url(
        settings.APP_ARCHIVE_BUCKET, 
        f"apps/{test_app.id}/test_archive.zip",
        content_type
    )

    r = await minio_client.put(
        upload_url,
        content=fake_archive_file,
        headers={"Content-Type": content_type}
    )
    test_app.archive_key = f"apps/{test_app.id}/test_archive.zip"
    await db_session.flush()
    await db_session.refresh(test_app)


class TestAppArchive:
    async def test_upload_app_archive(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB
    ):
        fake_archive_file = b"app data " * 100_000
        content_type = "application/zip"

        upload_url_response = await auth_client.post(
            f"/api/v1/app_archives/{test_app.id}/upload_url",
            json={
                "content_type": content_type, 
                "filename": "test_archive.zip"
            }
        )
        assert upload_url_response.status_code == 200
        upload_url = upload_url_response.json().get("upload_url")

        upload_minio_response = await minio_client.put(
            upload_url,
            content=fake_archive_file,
            headers={"Content-Type": content_type}
        )
        assert upload_minio_response.status_code == 200

        confirm_response = await auth_client.post(
            f"/api/v1/app_archives/{test_app.id}/confirm",
            json={"content_type": content_type}
        )
        assert confirm_response.status_code == 204

    async def test_upload_app_archive_wrong_content_type(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB
    ):
        upload_url_response = await auth_client.post(
            f"/api/v1/app_archives/{test_app.id}/upload_url",
            json={
                "content_type": "application/rar",
                "filename": "wrong_file"
            }
        )
        assert upload_url_response.status_code == 415

    async def test_download_app_archive(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB,
        db_session: AsyncSession,
        upload_test_archive: None
    ):
        download_response = await auth_client.get(
            f"/api/v1/app_archives/{test_app.id}/download_url"
        )
        assert download_response.status_code == 200
        download_url: str = download_response.json().get("download_url")

        archive_response = await minio_client.get(
            download_url
        )

        assert archive_response.status_code == 200
        assert len(archive_response.content) == 900_000
        assert archive_response.headers.get(
            "Content-Type"
        ) == "application/zip"
        assert "test_archive.zip" in download_url

    async def test_download_app_archive_not_purchased(
        self, 
        auth_client_2: AsyncClient,
        test_app: AppDB,
        upload_test_archive: None
    ):
        download_response = await auth_client_2.get(
            f"/api/v1/app_archives/{test_app.id}/download_url"
        )
        assert download_response.status_code == 403