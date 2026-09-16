from httpx import AsyncClient

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

from app.storage.minio_repo import MinioStorage

from app.models.app import AppDB
from app.models.app_cover import AppCoverDB


class TestMedia:
    async def test_upload_avatar(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient
    ):
        fake_avatar_file = b"image data " * 1024
        content_type = "image/png"

        upload_url_response = await auth_client.post(
            "/api/v1/media/users/me/avatar/upload_url",
            json={"content_type": content_type}
        )
        assert upload_url_response.status_code == 200
        upload_url = upload_url_response.json().get("upload_url")

        upload_minio_response = await minio_client.put(
            upload_url,
            content=fake_avatar_file,
            headers={"Content-Type": content_type}
        )
        assert upload_minio_response.status_code == 200

        confirm_response = await auth_client.post(
            "/api/v1/media/users/me/avatar/confirm",
            json={"content_type": content_type}
        )
        assert confirm_response.status_code == 201

        file_response = await minio_client.get(
            url=confirm_response.json().get("url")
        )
        assert len(file_response.content) == len(fake_avatar_file)
        assert file_response.headers.get("Content-Type") == content_type
            
    async def test_upload_avatar_wrong_type(
        self, 
        auth_client: AsyncClient
    ):
        upload_url_response = await auth_client.post(
            "/api/v1/media/users/me/avatar/upload_url",
            json={"content_type": "application/zip"}
        )
        assert upload_url_response.status_code == 415

    async def test_upload_app_icon(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB
    ):
        fake_icon_file = b"image data " * 1024
        content_type = "image/jpeg"

        upload_url_response = await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/icon/upload_url",
            json={"content_type": content_type}
        )
        assert upload_url_response.status_code == 200
        upload_url = upload_url_response.json().get("upload_url")

        upload_minio_response = await minio_client.put(
            upload_url,
            content=fake_icon_file,
            headers={"Content-Type": content_type}
        )
        assert upload_minio_response.status_code == 200

        confirm_response = await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/icon/confirm",
            json={"content_type": content_type}
        )
        assert confirm_response.status_code == 201

        file_response = await minio_client.get(
            url=confirm_response.json().get("url")
        )
        assert len(file_response.content) == len(fake_icon_file)
        assert file_response.headers.get("Content-Type") == content_type

    async def test_upload_app_cover(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB
    ):
        fake_image_file = b"image data " * 1024
        content_type = "image/webp"

        upload_url_response = await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/covers/upload_url",
            json={"content_type": content_type}
        )
        assert upload_url_response.status_code == 200
        upload_url = upload_url_response.json().get("upload_url")

        upload_minio_response = await minio_client.put(
            upload_url,
            content=fake_image_file,
            headers={"Content-Type": content_type}
        )
        assert upload_minio_response.status_code == 200

        confirm_response = await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/covers/confirm",
            json={"object_key": upload_url_response.json().get("object_key")}
        )
        assert confirm_response.status_code == 201

        file_response = await minio_client.get(
            url=confirm_response.json().get("url")
        )
        assert len(file_response.content) == len(fake_image_file)
        assert file_response.headers.get("Content-Type") == content_type

    async def test_delete_app_cover(
        self, 
        auth_client: AsyncClient,
        minio_client: AsyncClient,
        test_app: AppDB,
        object_storage: MinioStorage,
        db_session: AsyncSession
    ):
        fake_image_file = b"image data " * 1024
        content_type = "image/webp"

        upload_url_response = await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/covers/upload_url",
            json={"content_type": content_type}
        )
        upload_url = upload_url_response.json().get("upload_url")

        await minio_client.put(
            upload_url,
            content=fake_image_file,
            headers={"Content-Type": content_type}
        )

        await auth_client.post(
            f"/api/v1/media/apps/{test_app.id}/covers/confirm",
            json={"object_key": upload_url_response.json().get("object_key")}
        )

        covers_response = await auth_client.get(
            f"/api/v1/media/apps/{test_app.id}/covers"
        )
        data = covers_response.json()
        cover = data["covers"][0]

        cover = (await db_session.exec(
            select(AppCoverDB).where(AppCoverDB.app_id == test_app.id)
        )).first()

        delete_response = await auth_client.delete(
            f"/api/v1/media/apps/{test_app.id}/covers/{cover.id}"
        )
        cover_exists_in_minio = await object_storage.object_exists(
            settings.APP_COVER_BUCKET,
            cover.object_key
        )
        covers = (await db_session.exec(
            select(AppCoverDB).where(AppCoverDB.app_id == test_app.id)
            )
        ).all()

        assert delete_response.status_code == 204
        assert not cover_exists_in_minio
        assert len(covers) == 0