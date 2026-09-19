from httpx import AsyncClient


class TestServer:
    async def test_liveness_probe(self, client: AsyncClient):
        response = await client.get("/live")
        assert response.status_code == 200

    async def test_readiness_probe(self, client: AsyncClient):
        response = await client.get("/ready")
        data = response.json()

        assert response.status_code == 200
        assert all(
            status.lower() == "ok" 
            for status in data["services"].values()
        )
