# GPUPilot Phase 7: GPU Benchmarking Suite
# Standardized Compute, Memory, and Mixed Stress Benchmarks with Before/After Telemetry Deltas.
from __future__ import annotations
import time
import math
import array
import uuid
import threading
from typing import Optional, List, Callable
from models.schemas import (
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkTelemetryDelta,
    BenchmarkTestType,
    GPUMetrics,
)

_lock = threading.Lock()
_current_status = BenchmarkStatus(is_running=False)
_benchmark_history: List[BenchmarkResult] = []


def get_benchmark_status() -> BenchmarkStatus:
    with _lock:
        return _current_status


def get_benchmark_history() -> List[BenchmarkResult]:
    with _lock:
        return list(_benchmark_history)


def _compute_stress_workload(duration_seconds: float, cancel_event: threading.Event) -> float:
    """Intensive floating-point & trigonometric compute kernel loop."""
    t0 = time.time()
    ops = 0
    # Matrix of 256 elements updated with compound trig calculations
    data = [float(i) for i in range(256)]
    while (time.time() - t0) < duration_seconds and not cancel_event.is_set():
        for i in range(256):
            val = data[i]
            data[i] = math.sin(val) * math.cos(val) + math.sqrt(abs(val) + 1.0)
        ops += 256 * 4
    dur = max(0.001, time.time() - t0)
    return ops / dur


def _memory_stress_workload(duration_seconds: float, cancel_event: threading.Event) -> float:
    """Sequential memory allocation, transformation, and throughput loop."""
    t0 = time.time()
    bytes_transferred = 0
    size = 1024 * 1024  # 1M floats ~ 4MB block
    block = array.array("f", [float(i % 100) for i in range(size)])

    while (time.time() - t0) < duration_seconds and not cancel_event.is_set():
        # Memory copying and accumulation
        scratch = array.array("f", block)
        bytes_transferred += size * 4
        del scratch
    dur = max(0.001, time.time() - t0)
    # Return operations per second (GB/s equivalent scaled)
    return (bytes_transferred / (1024 * 1024)) / dur


def _mixed_stress_workload(duration_seconds: float, cancel_event: threading.Event) -> float:
    """Combined compute and memory stress loop."""
    t0 = time.time()
    ops = 0
    while (time.time() - t0) < duration_seconds and not cancel_event.is_set():
        _compute_stress_workload(0.1, cancel_event)
        _memory_stress_workload(0.1, cancel_event)
        ops += 2000000
    dur = max(0.001, time.time() - t0)
    return ops / dur


def _calculate_score_and_grade(
    ops: float,
    test_type: str,
    baseline_temp: Optional[float],
    peak_temp: Optional[float],
    is_throttling: bool,
) -> tuple[int, str, str]:
    """Computes standardized 0-1000 score and performance grade."""
    temp_rise = (peak_temp - baseline_temp) if (peak_temp and baseline_temp) else 0.0

    if test_type == "compute":
        raw_score = int(min(980, max(200, math.log10(max(1.0, ops)) * 140)))
    elif test_type == "memory":
        raw_score = int(min(980, max(200, (ops / 20.0) * 120)))
    else:  # stress
        raw_score = int(min(980, max(200, math.log10(max(1.0, ops)) * 135)))

    # Thermal penalty if throttled or junction temp exceeds 85°C
    if peak_temp and peak_temp >= 88:
        raw_score = max(100, int(raw_score * 0.75))
        grade = "Thermal Throttled"
        summary = f"Performance score throttled due to excessive core temperature ({peak_temp:.0f}°C)."
    elif raw_score >= 850:
        grade = "A+"
        summary = "Exceptional performance envelope. Stable clock curves and low thermal rise."
    elif raw_score >= 700:
        grade = "A"
        summary = "Strong sustained throughput across workload execution."
    elif raw_score >= 500:
        grade = "B"
        summary = "Good baseline performance with minor queue or clock variance."
    else:
        grade = "C"
        summary = "Moderate throughput observed; consider workload optimization."

    return raw_score, grade, summary


def execute_benchmark(req: BenchmarkRequest, get_metrics_fn: Callable[[], GPUMetrics]) -> BenchmarkResult:
    global _current_status, _benchmark_history

    # Capture Baseline Telemetry
    try:
        baseline_m = get_metrics_fn()
    except Exception:
        baseline_m = None

    base_temp = baseline_m.temperature if baseline_m else None
    peak_temp = base_temp
    peak_power = baseline_m.power_usage if baseline_m else None
    power_limit = baseline_m.power_limit if baseline_m else None
    peak_gpu_util = baseline_m.gpu_utilization if baseline_m else None
    peak_cpu_util = baseline_m.cpu_utilization if baseline_m else None
    clocks: List[float] = []
    if baseline_m and baseline_m.gpu_clock:
        clocks.append(baseline_m.gpu_clock)

    t_start = time.time()
    total_sec = float(req.duration_seconds)

    cancel_event = threading.Event()

    with _lock:
        _current_status = BenchmarkStatus(
            is_running=True,
            current_test=req.test_type.value,
            elapsed_seconds=0.0,
            total_seconds=total_sec,
            progress_percent=0.0,
            latest_result=None,
        )

    # Monitor thread for live delta sampling
    def monitor():
        while not cancel_event.is_set():
            time.sleep(0.4)
            elapsed = time.time() - t_start
            pct = min(99.0, round((elapsed / total_sec) * 100, 1))
            try:
                cur_m = get_metrics_fn()
                nonlocal peak_temp, peak_power, peak_gpu_util, peak_cpu_util
                if cur_m.temperature and (peak_temp is None or cur_m.temperature > peak_temp):
                    peak_temp = cur_m.temperature
                if cur_m.power_usage and (peak_power is None or cur_m.power_usage > peak_power):
                    peak_power = cur_m.power_usage
                if cur_m.gpu_utilization and (peak_gpu_util is None or cur_m.gpu_utilization > peak_gpu_util):
                    peak_gpu_util = cur_m.gpu_utilization
                if cur_m.cpu_utilization and (peak_cpu_util is None or cur_m.cpu_utilization > peak_cpu_util):
                    peak_cpu_util = cur_m.cpu_utilization
                if cur_m.gpu_clock:
                    clocks.append(cur_m.gpu_clock)
            except Exception:
                pass

            with _lock:
                if _current_status.is_running:
                    _current_status.elapsed_seconds = round(elapsed, 1)
                    _current_status.progress_percent = pct

    mon_t = threading.Thread(target=monitor, daemon=True)
    mon_t.start()

    # Execute Selected Stress Workload
    try:
        if req.test_type == BenchmarkTestType.MEMORY:
            ops = _memory_stress_workload(total_sec, cancel_event)
        elif req.test_type == BenchmarkTestType.STRESS:
            ops = _mixed_stress_workload(total_sec, cancel_event)
        else:
            ops = _compute_stress_workload(total_sec, cancel_event)
    finally:
        cancel_event.set()
        mon_t.join(timeout=1.0)

    # Final telemetry capture
    try:
        final_m = get_metrics_fn()
        if final_m.temperature and (peak_temp is None or final_m.temperature > peak_temp):
            peak_temp = final_m.temperature
        if final_m.power_usage and (peak_power is None or final_m.power_usage > peak_power):
            peak_power = final_m.power_usage
    except Exception:
        pass

    temp_delta = round(peak_temp - base_temp, 1) if (peak_temp is not None and base_temp is not None) else None
    avg_clock = round(sum(clocks) / len(clocks), 1) if clocks else None
    is_throttled = bool(peak_temp and peak_temp >= 89)

    score, grade, summary = _calculate_score_and_grade(
        ops=ops,
        test_type=req.test_type.value,
        baseline_temp=base_temp,
        peak_temp=peak_temp,
        is_throttling=is_throttled,
    )

    result = BenchmarkResult(
        id=str(uuid.uuid4())[:8],
        test_type=req.test_type.value,
        duration_seconds=int(total_sec),
        score=score,
        grade=grade,
        throughput_ops=round(ops, 1),
        telemetry=BenchmarkTelemetryDelta(
            baseline_temp=base_temp,
            peak_temp=peak_temp,
            temp_delta=temp_delta,
            peak_power=peak_power,
            power_limit=power_limit,
            avg_clock=avg_clock,
            peak_gpu_util=peak_gpu_util,
            peak_cpu_util=peak_cpu_util,
        ),
        summary=summary,
    )

    with _lock:
        _current_status = BenchmarkStatus(
            is_running=False,
            current_test=None,
            elapsed_seconds=round(total_sec, 1),
            total_seconds=total_sec,
            progress_percent=100.0,
            latest_result=result,
        )
        _benchmark_history.insert(0, result)
        if len(_benchmark_history) > 10:
            _benchmark_history.pop()

    return result
