# Phase 5: Bottleneck Detection Engine unit tests.
# Pure unit tests -- no HTTP, no hardware, no provider mocking.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.schemas import GPUMetrics
from gpu import diagnostics as engine


def _make_metrics(**kwargs) -> GPUMetrics:
    defaults = dict(
        vendor="TestVendor", name="Test GPU",
        gpu_utilization=30.0, memory_used=1.0, memory_total=8.0,
        memory_utilization=12.5, temperature=55.0, power_usage=60.0,
        power_limit=130.0, fan_speed=40.0, gpu_clock=1500.0,
        memory_clock=6000.0, cpu_utilization=20.0,
        latency=None, throughput=None,
    )
    defaults.update(kwargs)
    return GPUMetrics(**defaults)


# Healthy -------------------------------------------------------------------

def test_healthy_workload():
    m = _make_metrics(gpu_utilization=65.0, temperature=68.0, memory_utilization=40.0, cpu_utilization=25.0)
    r = engine.analyse(m)
    assert r.status == "healthy"
    assert r.bottleneck == engine.HEALTHY
    assert r.confidence >= 0.90
    assert len(r.recommendations) >= 1
    assert r.metrics_snapshot["gpu_utilization"] == 65.0


# Thermal -------------------------------------------------------------------

def test_thermal_warning_at_82():
    m = _make_metrics(temperature=82.0, gpu_utilization=70.0)
    r = engine.analyse(m)
    assert r.status == "warning"
    assert r.bottleneck == engine.THERMAL_THROTTLE
    assert r.severity == "high"
    assert r.confidence >= 0.85


def test_thermal_critical_at_92():
    m = _make_metrics(temperature=92.0, gpu_utilization=85.0)
    r = engine.analyse(m)
    assert r.status == "critical"
    assert r.bottleneck == engine.THERMAL_THROTTLE
    assert r.severity == "critical"
    assert r.confidence >= 0.95
    assert any("throttle" in rec.lower() or "cool" in rec.lower() or "workload" in rec.lower()
               for rec in r.recommendations)


def test_no_thermal_when_temp_is_none():
    m = _make_metrics(temperature=None, gpu_utilization=30.0, memory_utilization=20.0)
    r = engine.analyse(m)
    assert r.bottleneck != engine.THERMAL_THROTTLE


# VRAM exhaustion -----------------------------------------------------------

def test_vram_exhaustion_at_96_pct():
    m = _make_metrics(memory_utilization=96.0, memory_used=7.68, memory_total=8.0, temperature=70.0)
    r = engine.analyse(m)
    assert r.status == "critical"
    assert r.bottleneck == engine.VRAM_EXHAUSTION
    assert r.confidence >= 0.90


def test_vram_warning_at_91_pct():
    m = _make_metrics(memory_utilization=91.0, memory_used=7.28, memory_total=8.0, temperature=70.0)
    r = engine.analyse(m)
    assert r.status == "warning"
    assert r.bottleneck == engine.VRAM_EXHAUSTION


# Compute bottleneck --------------------------------------------------------

def test_compute_bound_at_97_pct():
    m = _make_metrics(gpu_utilization=97.0, memory_utilization=35.0, cpu_utilization=30.0, temperature=72.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.COMPUTE_BOUND
    assert r.status == "warning"
    assert r.confidence >= 0.85
    assert any("fp16" in rec.lower() or "precision" in rec.lower() or "int8" in rec.lower()
               for rec in r.recommendations)


def test_compute_bound_not_triggered_below_85():
    m = _make_metrics(gpu_utilization=80.0, temperature=65.0)
    r = engine.analyse(m)
    assert r.bottleneck != engine.COMPUTE_BOUND


# CPU starvation ------------------------------------------------------------

def test_cpu_starvation_cpu_high_gpu_low():
    m = _make_metrics(cpu_utilization=92.0, gpu_utilization=22.0, temperature=65.0, memory_utilization=20.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.CPU_STARVATION
    assert r.status == "warning"
    assert r.confidence >= 0.85


def test_cpu_starvation_not_triggered_when_gpu_high():
    m = _make_metrics(cpu_utilization=92.0, gpu_utilization=85.0, temperature=65.0)
    r = engine.analyse(m)
    assert r.bottleneck != engine.CPU_STARVATION


# Memory bandwidth ----------------------------------------------------------

def test_memory_bandwidth_bottleneck():
    m = _make_metrics(gpu_utilization=28.0, memory_utilization=65.0, cpu_utilization=30.0, temperature=60.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.MEMORY_BANDWIDTH
    assert r.severity == "medium"


# VRAM pressure -------------------------------------------------------------

# VRAM pressure fires when gpu_util >= 60 (so memory_bandwidth rule is skipped)
# and vram is 70-90%
def test_vram_pressure_70_to_90():
    m = _make_metrics(memory_utilization=78.0, gpu_utilization=65.0, cpu_utilization=25.0, temperature=60.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.VRAM_PRESSURE
    assert r.status == "warning"
    assert r.severity == "low"


# Priority ordering ---------------------------------------------------------

def test_thermal_takes_priority_over_vram():
    m = _make_metrics(temperature=91.0, memory_utilization=95.0, gpu_utilization=80.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.THERMAL_THROTTLE


def test_vram_exhaustion_takes_priority_over_compute():
    m = _make_metrics(temperature=70.0, memory_utilization=93.0, gpu_utilization=92.0, cpu_utilization=30.0)
    r = engine.analyse(m)
    assert r.bottleneck == engine.VRAM_EXHAUSTION


# Snapshot always present ---------------------------------------------------

def test_metrics_snapshot_in_result():
    m = _make_metrics(gpu_utilization=50.0, temperature=60.0)
    r = engine.analyse(m)
    snap = r.metrics_snapshot
    assert "gpu_utilization" in snap
    assert snap["gpu_utilization"] == 50.0
