# Phase 6: Optimization Recommendation Engine Unit Tests
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.schemas import GPUMetrics
from gpu import optimizer
from gpu import diagnostics as diag


def _make_metrics(**kwargs) -> GPUMetrics:
    defaults = dict(
        vendor="NVIDIA", name="Test RTX 3050",
        gpu_utilization=30.0, memory_used=1.0, memory_total=8.0,
        memory_utilization=12.5, temperature=55.0, power_usage=60.0,
        power_limit=130.0, fan_speed=40.0, gpu_clock=1500.0,
        memory_clock=6000.0, cpu_utilization=20.0,
        latency=None, throughput=None,
    )
    defaults.update(kwargs)
    return GPUMetrics(**defaults)


def test_thermal_optimization_recommendations():
    m = _make_metrics(temperature=92.0, gpu_utilization=85.0)
    plan = optimizer.generate_plan(m)
    assert plan.bottleneck == diag.THERMAL_THROTTLE
    assert plan.severity == "critical"
    assert len(plan.recommendations) >= 2
    assert any("nvidia-smi" in (r.code_snippet or "") for r in plan.recommendations)


def test_vram_optimization_recommendations():
    m = _make_metrics(memory_utilization=96.0, memory_used=7.68, memory_total=8.0)
    plan = optimizer.generate_plan(m)
    assert plan.bottleneck == diag.VRAM_EXHAUSTION
    assert any("gradient" in r.title.lower() or "batch" in r.title.lower() for r in plan.recommendations)


def test_compute_optimization_recommendations():
    m = _make_metrics(gpu_utilization=98.0, memory_utilization=40.0)
    plan = optimizer.generate_plan(m)
    assert plan.bottleneck == diag.COMPUTE_BOUND
    assert any("fp16" in r.title.lower() or "torch.compile" in (r.code_snippet or "") for r in plan.recommendations)


def test_cpu_starvation_optimization_recommendations():
    m = _make_metrics(cpu_utilization=92.0, gpu_utilization=20.0)
    plan = optimizer.generate_plan(m)
    assert plan.bottleneck == diag.CPU_STARVATION
    assert any("num_workers" in (r.code_snippet or "") for r in plan.recommendations)


def test_healthy_optimization_plan():
    m = _make_metrics(gpu_utilization=50.0, memory_utilization=30.0, temperature=55.0)
    plan = optimizer.generate_plan(m)
    assert plan.bottleneck == diag.HEALTHY
    assert len(plan.recommendations) >= 1
