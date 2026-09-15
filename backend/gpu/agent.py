# GPUPilot Phase 9: AI Agent / LLM Workload Explainer Layer
from __future__ import annotations
from typing import List
from models.schemas import GPUMetrics, AgentChatResponse
from gpu import diagnostics as diag


def explain_state(metrics: GPUMetrics, query: str = "") -> AgentChatResponse:
    diagnosis = diag.analyse(metrics)
    b_type = diagnosis.bottleneck
    gpu_name = metrics.name
    temp = metrics.temperature or 0.0
    util = metrics.gpu_utilization or 0.0
    vram = metrics.memory_utilization or 0.0
    cpu = metrics.cpu_utilization or 0.0

    # Question-specific answers
    q = query.lower()
    if "cpu hotter" in q or "temp" in q and "cpu" in q:
        explanation = (
            f"Your host CPU ({cpu:.0f}% load) operates inside a shared chassis cooling envelope with your {gpu_name}. "
            "In modern laptops (like ASUS VivoBook), the CPU package frequently reaches 85-95°C during high-framerate rendering or data prep "
            "while the dedicated GPU stays cooler (~{temp:.0f}°C). This happens because the CPU handles geometry calculation, driver draw calls, "
            "and browser execution, making it the primary thermal bottleneck."
        )
        actions = ["Parallelize data workers", "Limit background browser processes", "Elevate laptop rear for intake airflow"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    if "4gb" in q or "vram" in q:
        explanation = (
            f"On a 4GB VRAM accelerator like your {gpu_name}, dedicated memory is your most scarce resource. "
            f"Currently, VRAM occupancy is {vram:.1f}%. To prevent Out-of-Memory (OOM) fatal errors during model execution, "
            "always activate activation checkpointing (`model.gradient_checkpointing_enable()`), adopt INT8/4-bit quantization (BitsAndBytes), "
            "and utilize gradient accumulation instead of large micro-batches."
        )
        actions = ["Enable Gradient Checkpointing", "Apply INT8 Quantization", "Cut batch size in half"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    if "benchmark" in q or "score" in q:
        explanation = (
            "GPUPilot's composite benchmark score assesses compute stability, thermal resilience, and memory bus throughput. "
            f"With your {gpu_name} running at {util:.0f}% utilization and {temp:.0f}°C core temperature, the system exhibits stable clock maintenance. "
            "To maximize benchmark scores, ensure AC power is connected and set Windows/OEM battery plan to 'High Performance'."
        )
        actions = ["Run 10s Sustained Benchmark", "Check AC power adapter", "Set OEM Fan Profile to Maximum"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # General State Explanation based on active bottleneck
    if b_type == diag.THERMAL_THROTTLE:
        response = (
            f"⚠️ **Thermal Throttling Alert on {gpu_name}**\n\n"
            f"Core temperature is running high at **{temp:.0f}°C**. The internal silicon safety mechanism is actively downclocking "
            "core frequencies to protect the die from thermal degradation.\n\n"
            "**Recommended Fix:** Cap target power envelope down by 10-15% via NVML, clean fan exhaust vents, and elevate chassis."
        )
        actions = ["Cap Power Envelope (-15%)", "Max Out Cooling Fans", "Lower Workload Batch Queue"]
    elif b_type == diag.VRAM_EXHAUSTION:
        response = (
            f"💥 **Critical VRAM Allocation Hazard ({vram:.0f}% Occupancy)**\n\n"
            f"Your dedicated memory is near full capacity on {gpu_name}. Memory allocation fragmentation is severely increasing latency.\n\n"
            "**Recommended Fix:** Immediately enable activation checkpointing, downscale batch sizes, or load model in INT8/FP8."
        )
        actions = ["Downscale Batch Size", "Enable Activation Checkpointing", "Prune PyTorch Cache"]
    elif b_type == diag.CPU_STARVATION:
        response = (
            f"🖥️ **CPU Starvation Bottleneck Detected**\n\n"
            f"Host CPU load is pinned at **{cpu:.0f}%** while the {gpu_name} sits underutilized at only **{util:.0f}%**. "
            "The GPU is repeatedly stalling while waiting for the CPU to feed preprocessed batches.\n\n"
            "**Recommended Fix:** Increase DataLoader `num_workers=4`, use page-locked host memory (`pin_memory=True`), and move decoding directly to GPU."
        )
        actions = ["Tune DataLoader Workers", "Enable Pin Memory", "Offload Preprocessing to GPU"]
    elif b_type == diag.COMPUTE_BOUND:
        response = (
            f"⚡ **Compute Saturated ({util:.0f}% Utilization)**\n\n"
            f"The compute pipelines on your {gpu_name} are fully occupied. Throughput is compute-bound rather than memory-limited.\n\n"
            "**Recommended Fix:** Switch to FP16 Automatic Mixed Precision (AMP) to tap into Tensor Cores for a 2x-3x speedup."
        )
        actions = ["Enable FP16 Mixed Precision", "Compile with torch.compile()", "Optimize Kernel Alignment"]
    else:
        response = (
            f"✅ **System Operating Nominally**\n\n"
            f"Your {gpu_name} is in a balanced operating state ({util:.0f}% GPU, {temp:.0f}°C, {vram:.0f}% VRAM). "
            "No active performance anomalies or hardware constraints detected."
        )
        actions = ["Run Stress Benchmark", "Establish Baseline Telemetry", "Monitor Multi-Metric Charts"]

    return AgentChatResponse(response=response, suggested_actions=actions)
