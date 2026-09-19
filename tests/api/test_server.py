from httpx import AsyncClient


class TestServer:
    async def test_liveness_probe(self, client: AsyncClient):
        response = await client.get("/live")
        assert response.status_code == 200

    async def test_readiness_probe(self, client: AsyncClient):
        response = await client.get("/ready")
        data = response.json()
        services = data["services"]
  
        assert response.status_code == 503
        assert services["db"].lower() == services["redis"].lower() == "ok"
        assert "No active workers found" in services["celery"]
