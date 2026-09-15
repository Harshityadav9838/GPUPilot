# GPUPilot Phase 5 -- Bottleneck Detection Engine.
# Deterministic rules engine: analyses a GPUMetrics snapshot and returns
# a BottleneckResult. Rules run in priority order (most critical first).
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from models.schemas import GPUMetrics

# Bottleneck type constants
HEALTHY          = "none"
THERMAL_THROTTLE = "thermal_throttling"
VRAM_EXHAUSTION  = "vram_exhaustion"
COMPUTE_BOUND    = "compute_bound"
CPU_STARVATION   = "cpu_starvation"
MEMORY_BANDWIDTH = "memory_bandwidth"
VRAM_PRESSURE    = "vram_pressure"
UNKNOWN          = "unknown"


@dataclass
class BottleneckResult:
    status: str                         # "healthy" | "warning" | "critical"
    bottleneck: str                     # one of the constants above
    confidence: float                   # 0.0 - 1.0
    severity: str                       # "ok" | "low" | "medium" | "high" | "critical"
    title: str                          # short human label
    explanation: str                    # 1-2 sentence description
    recommendations: List[str]          # ordered action list
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)


def _pct(value: Optional[float], fallback: float = 0.0) -> float:
    return float(value) if value is not None else fallback

def _confidence(base: float, signal: float) -> float:
    return round(min(0.99, max(0.50, base + signal)), 2)

def _snapshot(m: GPUMetrics) -> Dict[str, Any]:
    return {
        "gpu_utilization":  m.gpu_utilization,
        "memory_utilization": m.memory_utilization,
        "memory_used_gb":   m.memory_used,
        "memory_total_gb":  m.memory_total,
        "temperature":      m.temperature,
        "power_usage":      m.power_usage,
        "power_limit":      m.power_limit,
        "cpu_utilization":  m.cpu_utilization,
        "gpu_clock":        m.gpu_clock,
        "fan_speed":        m.fan_speed,
    }


# ── Rules ─────────────────────────────────────────────────────────────────

def _rule_thermal(m: GPUMetrics) -> Optional[BottleneckResult]:
    # Thermal throttle: temperature >= 80 C
    temp = m.temperature
    if temp is None:
        return None
    if temp >= 90:
        sig = min(0.08, (temp - 90) * 0.008)
        return BottleneckResult(
            status="critical", bottleneck=THERMAL_THROTTLE,
            confidence=_confidence(0.96, sig), severity="critical",
            title="Thermal Throttling — Critical",
            explanation=(
                f"GPU temperature is {temp:.0f} C — above the 90 C throttle boundary. "
                "Hardware is reducing core clocks to prevent damage."
            ),
            recommendations=[
                "Immediately reduce workload or power limit",
                "Clean dust from heatsink and fans",
                "Verify chassis airflow (intake to exhaust)",
                "Re-apply thermal paste if temps persist after cleaning",
                "Consider undervolting via MSI Afterburner / AMD Software",
            ],
            metrics_snapshot=_snapshot(m),
        )
    if temp >= 80:
        sig = min(0.06, (temp - 80) * 0.006)
        return BottleneckResult(
            status="warning", bottleneck=THERMAL_THROTTLE,
            confidence=_confidence(0.88, sig), severity="high",
            title="Thermal Stress — Approaching Throttle Limit",
            explanation=(
                f"GPU temperature is {temp:.0f} C, approaching the 90 C throttle boundary. "
                "Sustained load may cause clock-speed reductions and latency spikes."
            ),
            recommendations=[
                "Monitor temperature trend over the next few minutes",
                "Ensure cooling fans are running at full speed",
                "Reduce ambient temperature or improve case ventilation",
                "Lower power limit by 10-15% as a precaution",
            ],
            metrics_snapshot=_snapshot(m),
        )
    return None


def _rule_vram_exhaustion(m: GPUMetrics) -> Optional[BottleneckResult]:
    # VRAM near-OOM: memory_utilization >= 90%
    vram_pct = _pct(m.memory_utilization)
    if vram_pct < 90:
        return None
    sig = min(0.06, (vram_pct - 90) * 0.006)
    used = m.memory_used or 0
    total = m.memory_total or 0
    is_critical = vram_pct >= 95
    return BottleneckResult(
        status="critical" if is_critical else "warning",
        bottleneck=VRAM_EXHAUSTION,
        confidence=_confidence(0.93, sig),
        severity="critical" if is_critical else "high",
        title="VRAM Exhaustion Risk" + (" — OOM Imminent" if is_critical else ""),
        explanation=(
            f"VRAM usage is {vram_pct:.0f}% ({used:.2f} GB / {total:.2f} GB). "
            "Out-of-Memory (OOM) crashes can occur at 100% — allocation headroom is critically low."
        ),
        recommendations=[
            "Reduce batch size immediately",
            "Enable gradient checkpointing (deep learning workloads)",
            "Offload optimizer states to CPU RAM (ZeRO / DeepSpeed)",
            "Use FP16 / INT8 quantization to halve memory footprint",
            "Close other GPU-resident applications (games, browsers on GPU)",
        ],
        metrics_snapshot=_snapshot(m),
    )


def _rule_compute_bound(m: GPUMetrics) -> Optional[BottleneckResult]:
    # Compute bottleneck: gpu_utilization >= 85% with healthy VRAM
    gpu_util = _pct(m.gpu_utilization)
    cpu_util = _pct(m.cpu_utilization)
    if gpu_util < 85:
        return None
    # Defer to cpu_starvation if CPU also high and GPU not pegged
    if cpu_util >= 80 and gpu_util < 92:
        return None
    sig = min(0.08, (gpu_util - 85) * 0.008)
    return BottleneckResult(
        status="warning", bottleneck=COMPUTE_BOUND,
        confidence=_confidence(0.89, sig),
        severity="high" if gpu_util >= 95 else "medium",
        title="Compute Bottleneck — GPU Saturated",
        explanation=(
            f"GPU core utilization is {gpu_util:.0f}%, meaning compute throughput is maxed out. "
            "Adding more work will increase queue depth, not speed."
        ),
        recommendations=[
            "Switch to FP16 or BF16 mixed precision to double throughput",
            "Apply INT8 quantization for inference workloads",
            "Profile with NVIDIA Nsight / AMD GPU Profiler to find hot kernels",
            "Increase batch size to amortize GPU kernel launch overhead",
            "Evaluate tensor parallelism across multiple GPUs",
        ],
        metrics_snapshot=_snapshot(m),
    )


def _rule_cpu_starvation(m: GPUMetrics) -> Optional[BottleneckResult]:
    # CPU bottleneck: CPU pinned high, GPU underutilized
    gpu_util = _pct(m.gpu_utilization)
    cpu_util = _pct(m.cpu_utilization)
    if cpu_util < 80 or gpu_util >= 60:
        return None
    sig = min(0.08, (cpu_util - 80) * 0.008) + min(0.04, (60 - gpu_util) * 0.002)
    return BottleneckResult(
        status="warning", bottleneck=CPU_STARVATION,
        confidence=_confidence(0.87, sig),
        severity="high" if cpu_util >= 92 else "medium",
        title="CPU Starvation — GPU Waiting for Data",
        explanation=(
            f"Host CPU utilization is {cpu_util:.0f}% while GPU sits at only {gpu_util:.0f}%. "
            "The CPU cannot feed data fast enough, leaving GPU compute engines idle."
        ),
        recommendations=[
            "Increase DataLoader num_workers (PyTorch / TF datasets)",
            "Pin memory in DataLoader (pin_memory=True) for faster H-to-D copies",
            "Pre-process and cache training data offline",
            "Use GPU-accelerated decoding (NVJPEG, DALI, cuDNN)",
            "Profile CPU hotspots with py-spy or cProfile",
        ],
        metrics_snapshot=_snapshot(m),
    )


def _rule_memory_bandwidth(m: GPUMetrics) -> Optional[BottleneckResult]:
    # Memory-bandwidth bottleneck: low GPU util + elevated VRAM usage
    gpu_util = _pct(m.gpu_utilization)
    vram_pct = _pct(m.memory_utilization)
    if gpu_util >= 60 or vram_pct < 50:
        return None
    sig = min(0.06, (vram_pct - 50) * 0.003) + min(0.04, (60 - gpu_util) * 0.002)
    return BottleneckResult(
        status="warning", bottleneck=MEMORY_BANDWIDTH,
        confidence=_confidence(0.79, sig), severity="medium",
        title="Memory Bandwidth Bottleneck",
        explanation=(
            f"GPU utilization is low ({gpu_util:.0f}%) yet VRAM occupancy is {vram_pct:.0f}%. "
            "Memory access patterns are likely non-coalesced or repeatedly transferring large tensors."
        ),
        recommendations=[
            "Profile memory access patterns -- look for scatter/gather operations",
            "Minimise host-to-device transfers inside training loops",
            "Enable fused operations (torch.compile, XLA, cuBLAS fusion)",
            "Ensure tensor contiguity: call .contiguous() before large transfers",
            "Consider Flash Attention for attention-heavy models",
        ],
        metrics_snapshot=_snapshot(m),
    )


def _rule_vram_pressure(m: GPUMetrics) -> Optional[BottleneckResult]:
    # Elevated but not critical VRAM: 70-90%
    vram_pct = _pct(m.memory_utilization)
    if vram_pct < 70 or vram_pct >= 90:
        return None
    return BottleneckResult(
        status="warning", bottleneck=VRAM_PRESSURE,
        confidence=_confidence(0.75, min(0.05, (vram_pct - 70) * 0.0025)),
        severity="low",
        title="VRAM Pressure — Headroom Narrowing",
        explanation=(
            f"VRAM usage is {vram_pct:.0f}%, which is elevated. "
            "There is still headroom before OOM, but memory spikes could push over the limit."
        ),
        recommendations=[
            "Monitor VRAM trend — if climbing, reduce batch size",
            "Free unused tensors (del tensor; torch.cuda.empty_cache())",
            "Use gradient accumulation to simulate larger batches with less VRAM",
        ],
        metrics_snapshot=_snapshot(m),
    )


def _rule_healthy(m: GPUMetrics) -> BottleneckResult:
    # Fallback: system is healthy
    gpu_util = _pct(m.gpu_utilization)
    vram_pct = _pct(m.memory_utilization)
    temp = m.temperature
    parts = []
    if m.gpu_utilization is not None: parts.append(f"GPU {gpu_util:.0f}%")
    if temp is not None:              parts.append(f"Temp {temp:.0f} C")
    if m.memory_utilization is not None: parts.append(f"VRAM {vram_pct:.0f}%")
    summary = " | ".join(parts) if parts else "metrics nominal"
    return BottleneckResult(
        status="healthy", bottleneck=HEALTHY,
        confidence=0.97, severity="ok",
        title="System Healthy",
        explanation=(
            f"All telemetry is within optimal operating parameters ({summary}). "
            "No bottlenecks detected at this time."
        ),
        recommendations=[
            "System is performing optimally -- no action required",
            "Continue monitoring for trend changes",
        ],
        metrics_snapshot=_snapshot(m),
    )


# ── Rule pipeline (highest priority first) ────────────────────────────────
_RULES = [
    _rule_thermal,
    _rule_vram_exhaustion,
    _rule_compute_bound,
    _rule_cpu_starvation,
    _rule_memory_bandwidth,
    _rule_vram_pressure,
]


def analyse(metrics: GPUMetrics) -> BottleneckResult:
    # Run the full bottleneck rule pipeline. Returns first triggered result.
    for rule in _RULES:
        result = rule(metrics)
        if result is not None:
            return result
    return _rule_healthy(metrics)
