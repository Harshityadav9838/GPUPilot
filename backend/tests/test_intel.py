"""
Phase 4: Intel GPU Provider Tests.

Tests cover:
  1. Fallback when no Intel GPU is present (WMI returns no Intel adapter).
  2. Full happy-path with mocked WMI + perf-counter responses.
  3. Per-sensor failure resilience (each metric falls back to None independently).
"""

import sys
import json
import time
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wmi_json(name="Intel(R) UHD Graphics", driver="32.0.101.5768", ram=2147479552):
    """Return a JSON string as WMI would output for a single Intel adapter."""
    return json.dumps([
        {"Name": name, "DriverVersion": driver, "AdapterRAM": ram},
        {"Name": "NVIDIA GeForce RTX 3050 4GB Laptop GPU", "DriverVersion": "32.0.15.9597", "AdapterRAM": 4293918720},
    ])


def _make_luid_json(luid="0x00000000_0x000112cd"):
    """Return JSON with counter instances for the given LUID."""
    return json.dumps([
        {"InstanceName": f"pid_4_luid_{luid}_phys_0_eng_0_engtype_3d"},
        {"InstanceName": f"pid_100_luid_{luid}_phys_0_eng_1_engtype_3d"},
        {"InstanceName": "pid_4_luid_0x00000000_0x00011645_phys_0_eng_0_engtype_3d"},
    ])


# ---------------------------------------------------------------------------
# Test 1: Fallback when Intel GPU absent
# ---------------------------------------------------------------------------

def test_intel_unavailable_when_no_intel_wmi():
    """IntelProvider.is_available() is False when _init_intel finds no Intel GPU."""
    import gpu.intel as intel_mod

    # Patch _init_intel so it does nothing (simulates: _detect_intel_gpu returns None)
    with patch.object(intel_mod.IntelProvider, "_init_intel", lambda self: None):
        p = intel_mod.IntelProvider()

    # _available starts as False; _init_intel was skipped, so it stays False
    assert not p.is_available()
    info = p.get_info()
    assert info.vendor == "Intel"
    assert info.available is False


# ---------------------------------------------------------------------------
# Test 2: Happy path — Intel UHD Graphics detected and metrics returned
# ---------------------------------------------------------------------------

def test_intel_happy_path():
    """
    IntelProvider returns correct info & live metrics when Intel GPU is present.
    All PS commands are mocked to avoid hardware dependency.
    """
    LUID = "0x00000000_0x000112cd"
    call_sequence = [
        _make_wmi_json(),           # _detect_intel_gpu
        _make_luid_json(LUID),      # _get_intel_luid
        "14.9",                     # _query_gpu_utilization (sum of 3D engines)
        "0.0",                      # _query_memory - used_gb raw bytes -> "0"
        "1403297587.2",             # _query_memory - total committed bytes
    ]
    call_iter = iter(call_sequence)

    def mock_run_ps(cmd, timeout=10):
        return next(call_iter, None)

    with patch("gpu.intel._run_ps", side_effect=mock_run_ps),          patch("psutil.cpu_percent", return_value=12.3):

        from importlib import reload
        import gpu.intel as intel_mod
        reload(intel_mod)
        p = intel_mod.IntelProvider()

    assert p.is_available(), "Intel GPU should be available"

    info = p.get_info()
    assert info.vendor == "Intel"
    assert info.name == "Intel(R) UHD Graphics"
    assert info.driver_version == "32.0.101.5768"
    assert info.available is True
    assert info.is_demo is False
    assert info.details.get("luid") == LUID

    # Now mock the metric calls independently
    call_sequence2 = [
        "14.9",         # gpu utilization
        "0.0",          # memory used (bytes)
        "1403297587.2", # memory total committed (bytes)
    ]
    call_iter2 = iter(call_sequence2)

    with patch("gpu.intel._run_ps", side_effect=lambda cmd, timeout=10: next(call_iter2, None)),          patch("psutil.cpu_percent", return_value=12.3):
        metrics = p.get_metrics()

    assert metrics.vendor == "Intel"
    assert metrics.name == "Intel(R) UHD Graphics"
    assert metrics.gpu_utilization == 14.9
    assert metrics.cpu_utilization == 12.3
    # temperature / power / fan / clocks must be None (not available via DXGI)
    assert metrics.temperature is None
    assert metrics.power_usage is None
    assert metrics.fan_speed is None
    assert metrics.gpu_clock is None
    assert metrics.memory_clock is None
    assert metrics.timestamp > 0


# ---------------------------------------------------------------------------
# Test 3: Per-sensor failure resilience
# ---------------------------------------------------------------------------

def test_intel_sensor_failure_returns_none():
    """
    When any perf-counter PS call fails (returns None), that metric should
    be None in the result — not raise an exception.
    """
    LUID = "0x00000000_0x000112cd"

    # Init with valid WMI + LUID
    init_calls = iter([_make_wmi_json(), _make_luid_json(LUID)])

    with patch("gpu.intel._run_ps", side_effect=lambda cmd, timeout=10: next(init_calls, None)):
        from importlib import reload
        import gpu.intel as intel_mod
        reload(intel_mod)
        p = intel_mod.IntelProvider()

    assert p.is_available()

    # All metric queries fail
    with patch("gpu.intel._run_ps", return_value=None),          patch("psutil.cpu_percent", side_effect=Exception("psutil fail")):
        metrics = p.get_metrics()

    assert metrics.gpu_utilization is None
    assert metrics.memory_used is None
    assert metrics.memory_total is None
    assert metrics.memory_utilization is None
    assert metrics.cpu_utilization is None
    # No exception raised - this is the key assertion
