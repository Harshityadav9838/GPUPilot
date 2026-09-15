import sys
import types
import pytest
from gpu.amd import AMDProvider

def test_amd_fallback_on_unsupported_host():
    """Verify that on machines without AMD SMI, AMDProvider fails safely without crashing."""
    provider = AMDProvider()
    assert provider.is_available() is False
    info = provider.get_info()
    assert info.vendor == "AMD"
    assert info.available is False
    assert info.is_demo is False
    with pytest.raises(RuntimeError):
        provider.get_metrics()

def test_amd_provider_with_mocked_amdsmi(monkeypatch):
    """
    Verify that when amdsmi is present, AMDProvider extracts standardized metrics
    from an AMD accelerator (e.g. AMD Radeon RX 7900 XTX).
    """
    mock_amdsmi = types.ModuleType("amdsmi")
    
    # Mock Temperature Types
    class MockTempType:
        EDGE = 0
        JUNCTION = 1
    class MockTempMetric:
        CURRENT = 0
    class MockClkType:
        GFX = 0
        MEM = 1

    mock_amdsmi.AmdSmiTemperatureType = MockTempType
    mock_amdsmi.AmdSmiTemperatureMetric = MockTempMetric
    mock_amdsmi.AmdSmiClkType = MockClkType

    mock_amdsmi.amdsmi_init = lambda: None
    mock_amdsmi.amdsmi_shut_down = lambda: None
    mock_amdsmi.amdsmi_get_processor_handles = lambda: ["fake_amd_processor_handle_0"]
    mock_amdsmi.amdsmi_get_gpu_device_name = lambda handle: "AMD Radeon RX 7900 XTX"
    mock_amdsmi.amdsmi_get_driver_info = lambda: {"driver_version": "ROCm 6.0"}
    
    mock_amdsmi.amdsmi_get_gpu_activity = lambda handle: {
        "gfx_activity": 78.5,
        "umc_activity": 45.0
    }
    mock_amdsmi.amdsmi_get_gpu_vram_usage = lambda handle: {
        "vram_used": int(14.2 * (1024 ** 3)),
        "vram_total": int(24.0 * (1024 ** 3))
    }
    mock_amdsmi.amdsmi_get_temp_metric = lambda handle, sensor, metric: 65.0
    mock_amdsmi.amdsmi_get_power_info = lambda handle: {
        "current_socket_power": 280.0,
        "power_limit": 355.0
    }
    mock_amdsmi.amdsmi_get_gpu_fan_speed = lambda handle, sensor: 52.0
    mock_amdsmi.amdsmi_get_clock_info = lambda handle, clk_type: {
        "cur_clk": 2300.0 if clk_type == MockClkType.GFX else 2500.0
    }

    monkeypatch.setitem(sys.modules, "amdsmi", mock_amdsmi)

    # Instantiate provider with mocked amdsmi
    provider = AMDProvider()
    assert provider.is_available() is True
    
    info = provider.get_info()
    assert info.vendor == "AMD"
    assert info.name == "AMD Radeon RX 7900 XTX"
    assert info.driver_version == "ROCm 6.0"
    assert info.available is True
    assert info.details["total_vram_gb"] == 24.0

    metrics = provider.get_metrics()
    assert metrics.vendor == "AMD"
    assert metrics.name == "AMD Radeon RX 7900 XTX"
    assert metrics.gpu_utilization == 78.5
    assert metrics.memory_used == 14.2
    assert metrics.memory_total == 24.0
    assert metrics.memory_utilization == 59.2
    assert metrics.temperature == 65.0
    assert metrics.power_usage == 280.0
    assert metrics.power_limit == 355.0
    assert metrics.fan_speed == 52.0
    assert metrics.gpu_clock == 2300.0
    assert metrics.memory_clock == 2500.0
    assert metrics.latency is None
    assert metrics.throughput is None
    assert metrics.timestamp > 0

def test_amd_per_sensor_safe_fallback(monkeypatch):
    """
    Verify that if individual sensors (e.g. fan speed or power) raise exceptions,
    the provider sets them to None (null in JSON) rather than crashing.
    """
    mock_amdsmi = types.ModuleType("amdsmi")
    mock_amdsmi.amdsmi_init = lambda: None
    mock_amdsmi.amdsmi_shut_down = lambda: None
    mock_amdsmi.amdsmi_get_processor_handles = lambda: ["fake_handle"]
    mock_amdsmi.amdsmi_get_gpu_device_name = lambda h: "AMD Instinct MI300"
    mock_amdsmi.amdsmi_get_driver_info = lambda: {"driver_version": "ROCm 6.1"}
    
    # Faulty sensors
    mock_amdsmi.amdsmi_get_gpu_activity = lambda h: {"gfx_activity": 92.0}
    mock_amdsmi.amdsmi_get_gpu_vram_usage = lambda h: {"vram_used": int(64 * (1024**3)), "vram_total": int(192 * (1024**3))}
    def faulty_temp(*args): raise RuntimeError("Temperature sensor not accessible")
    def faulty_fan(*args): raise RuntimeError("Fan speed not supported (Passively cooled)")
    def faulty_power(*args): raise RuntimeError("Power monitoring disabled")
    
    mock_amdsmi.amdsmi_get_temp_metric = faulty_temp
    mock_amdsmi.amdsmi_get_gpu_fan_speed = faulty_fan
    mock_amdsmi.amdsmi_get_power_info = faulty_power
    mock_amdsmi.amdsmi_get_clock_info = lambda h, t: {}

    monkeypatch.setitem(sys.modules, "amdsmi", mock_amdsmi)

    provider = AMDProvider()
    assert provider.is_available() is True
    metrics = provider.get_metrics()
    
    assert metrics.gpu_utilization == 92.0
    assert metrics.temperature is None
    assert metrics.fan_speed is None
    assert metrics.power_usage is None
    assert metrics.power_limit is None
    assert metrics.gpu_clock is None
