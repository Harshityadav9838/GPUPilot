# Phase 7: GPU Benchmarking Engine Unit Tests
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.schemas import BenchmarkRequest, BenchmarkTestType, GPUMetrics
from gpu import benchmark


def _mock_metrics() -> GPUMetrics:
    return GPUMetrics(
        vendor="NVIDIA",
        name="RTX 3050 Laptop GPU",
        gpu_utilization=45.0,
        memory_used=1.2,
        memory_total=4.0,
        memory_utilization=30.0,
        temperature=60.0,
        power_usage=14.0,
        power_limit=45.0,
        cpu_utilization=35.0,
        gpu_clock=800.0,
    )


def test_compute_benchmark_execution():
    req = BenchmarkRequest(test_type=BenchmarkTestType.COMPUTE, duration_seconds=3)
    res = benchmark.execute_benchmark(req, _mock_metrics)
    assert res.score >= 100
    assert res.grade in ["A+", "A", "B", "C", "Thermal Throttled"]
    assert res.throughput_ops > 0
    assert res.telemetry.baseline_temp == 60.0


def test_memory_benchmark_execution():
    req = BenchmarkRequest(test_type=BenchmarkTestType.MEMORY, duration_seconds=3)
    res = benchmark.execute_benchmark(req, _mock_metrics)
    assert res.test_type == "memory"
    assert res.throughput_ops > 0


def test_benchmark_status_and_history():
    history = benchmark.get_benchmark_history()
    assert len(history) >= 1
    assert history[0].id is not None
    status = benchmark.get_benchmark_status()
    assert not status.is_running
    assert status.latest_result is not None
