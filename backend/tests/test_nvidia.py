import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from gpu.nvidia import NVIDIAProvider
from gpu.detector import detect_gpu, set_provider_mode

@pytest.mark.anyio
async def test_nvidia_provider_direct():
    provider = NVIDIAProvider()
    if provider.is_available():
        info = provider.get_info()
        assert info.vendor == "NVIDIA"
        assert info.is_demo is False
        assert info.available is True
        assert "RTX" in info.name or "NVIDIA" in info.name

        metrics = provider.get_metrics()
        assert metrics.vendor == "NVIDIA"
        assert metrics.memory_total > 0
        assert metrics.temperature is not None
        assert metrics.temperature > 0
        # Fan speed can be None on laptops or float on desktop cards
        assert metrics.fan_speed is None or (0 <= metrics.fan_speed <= 100)

@pytest.mark.anyio
async def test_nvidia_provider_fallback_when_disabled(monkeypatch):
    import pynvml
    # Simulate system without NVIDIA NVML
    def mock_nvml_init():
        raise RuntimeError("NVML Shared Library Not Found")
    
    monkeypatch.setattr(pynvml, "nvmlInit", mock_nvml_init)
    
    p = NVIDIAProvider()
    assert p.is_available() is False
    info = p.get_info()
    assert info.available is False
    with pytest.raises(RuntimeError):
        p.get_metrics()

@pytest.mark.anyio
async def test_api_mode_switching():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Switch to demo mode
        resp_demo = await ac.post("/provider/mode", json={"mode": "demo"})
        assert resp_demo.status_code == 200
        assert resp_demo.json()["active_mode"] == "demo"
        assert resp_demo.json()["is_demo"] is True

        # Check /metrics returns Demo
        m_demo = await ac.get("/metrics")
        assert m_demo.status_code == 200
        assert m_demo.json()["vendor"] == "Demo"

        # Switch to hardware mode
        resp_hw = await ac.post("/provider/mode", json={"mode": "hardware"})
        assert resp_hw.status_code == 200
        assert resp_hw.json()["active_mode"] == "hardware"
        assert resp_hw.json()["is_demo"] is False

        # Check /metrics returns NVIDIA
        m_hw = await ac.get("/metrics")
        assert m_hw.status_code == 200
        assert m_hw.json()["vendor"] == "NVIDIA"
