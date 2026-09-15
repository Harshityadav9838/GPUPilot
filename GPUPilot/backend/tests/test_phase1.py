import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from gpu.demo import DemoProvider
from models.schemas import DemoScenario

@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "active_provider" in data
    assert "is_demo" in data

@pytest.mark.anyio
async def test_gpu_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/gpu")
    assert response.status_code == 200
    data = response.json()
    assert "vendor" in data
    assert "name" in data
    assert "provider_type" in data

@pytest.mark.anyio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "gpu_utilization" in data
    assert "memory_used" in data
    assert "memory_total" in data
    assert "temperature" in data
    assert "power_usage" in data

@pytest.mark.anyio
async def test_demo_scenario_switch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Switch to thermal problem
        resp = await ac.post("/demo/scenario", json={"scenario": "thermal_problem"})
        assert resp.status_code == 200
        assert resp.json()["active_scenario"] == "thermal_problem"

        # Check metrics reflect higher temperature
        metrics_resp = await ac.get("/metrics")
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert metrics["temperature"] > 80.0
        assert metrics["fan_speed"] == 100.0

        # Switch back to healthy
        resp2 = await ac.post("/demo/scenario", json={"scenario": "healthy"})
        assert resp2.status_code == 200
