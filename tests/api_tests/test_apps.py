from httpx import AsyncClient
import pytest

from app.models.app import AppDB


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
        response = await auth_client.patch(
            f"/api/v1/apps/{test_app.id}", json=update_data
        )
        data = response.json()

        assert response.status_code == expected_status_code
        for key in expected_data.keys():
            assert data[key] == expected_data[key]

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
        assert len(data) == 11
        assert "genre" not in data

    async def test_get_private_app(
        self, client: AsyncClient, test_app_private: AppDB
    ):
        response = await client.get(f"/api/v1/apps/{test_app_private.id}")
        assert response.status_code == 404

    async def test_get_apps(self, client: AsyncClient, test_apps: list[AppDB]):
        query = {"search_query": ["APP", "Test", " free! "]}
        response = await client.get("/api/v1/apps", params=query)
        assert response.status_code == 200
