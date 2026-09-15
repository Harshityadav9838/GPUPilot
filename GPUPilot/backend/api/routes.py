from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.schemas import (
    HealthResponse,
    GPUInfo,
    GPUMetrics,
    SetScenarioRequest,
    ScenarioInfo,
    DemoScenario,
    DiagnoseResponse
)
from gpu.detector import get_active_provider
from gpu.demo import DemoProvider
from config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint providing API status and active provider."""
    provider = get_active_provider()
    info = provider.get_info()
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        active_provider=info.provider_type,
        is_demo=info.is_demo
    )

@router.get("/gpu", response_model=GPUInfo)
def get_gpu():
    """Returns detected GPU hardware details and provider information."""
    provider = get_active_provider()
    return provider.get_info()

@router.get("/metrics", response_model=GPUMetrics)
def get_metrics():
    """Returns real-time standardized GPU metrics."""
    provider = get_active_provider()
    try:
        return provider.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")

@router.get("/demo/scenarios", response_model=List[ScenarioInfo])
def list_demo_scenarios():
    """List available simulated scenarios for Demo Mode."""
    return [
        ScenarioInfo(
            id=DemoScenario.HEALTHY,
            name="Healthy Workload",
            description="Optimal balanced utilization (~68%), safe temperature and low latency."
        ),
        ScenarioInfo(
            id=DemoScenario.COMPUTE_BOTTLENECK,
            name="Compute Bottleneck",
            description="GPU utilization pinned near 98%, high power draw, compute-bound kernels."
        ),
        ScenarioInfo(
            id=DemoScenario.MEMORY_BOTTLENECK,
            name="Memory Bottleneck",
            description="Low GPU utilization (~41%) with high memory pressure and transfer stalls."
        ),
        ScenarioInfo(
            id=DemoScenario.CPU_BOTTLENECK,
            name="CPU Starvation Bottleneck",
            description="Host CPU pinned >90% while GPU waits starved with low utilization (~24%)."
        ),
        ScenarioInfo(
            id=DemoScenario.THERMAL_PROBLEM,
            name="Thermal Throttling",
            description="Critical temperatures (~90?C), max fan speed (100%), and reduced core clock."
        ),
        ScenarioInfo(
            id=DemoScenario.VRAM_PRESSURE,
            name="VRAM OOM Pressure",
            description="VRAM usage >95% causing thrashing, high latency spikes, and low throughput."
        )
    ]

@router.post("/demo/scenario")
def set_demo_scenario(req: SetScenarioRequest):
    """Switch the current simulation scenario in Demo Mode."""
    provider = get_active_provider()
    if isinstance(provider, DemoProvider):
        provider.set_scenario(req.scenario)
        return {"status": "success", "active_scenario": req.scenario.value}
    raise HTTPException(status_code=400, detail="Active provider is not in Demo Mode.")

# Future phase placeholders (returns helpful mock/stub responses in Phase 1)
@router.get("/diagnose", response_model=DiagnoseResponse)
def get_diagnosis():
    """
    Bottleneck diagnostic endpoint (Phase 5 preview).
    Dynamically mirrors the active demo scenario if in demo mode.
    """
    provider = get_active_provider()
    if isinstance(provider, DemoProvider):
        s = provider.scenario
        if s == DemoScenario.HEALTHY:
            return DiagnoseResponse(
                status="healthy",
                bottleneck="none",
                confidence=0.98,
                explanation="Workload is operating within optimal thermal and compute parameters.",
                recommendations=["System operating normally", "No action needed"]
            )
        elif s == DemoScenario.COMPUTE_BOTTLENECK:
            return DiagnoseResponse(
                status="warning",
                bottleneck="compute_bound",
                confidence=0.92,
                explanation="GPU core utilization is pinned near 98% while memory capacity is stable.",
                recommendations=["Consider FP16/BF16 mixed precision", "Evaluate INT8 quantization", "Optimize compute kernel efficiency"]
            )
        elif s == DemoScenario.MEMORY_BOTTLENECK:
            return DiagnoseResponse(
                status="warning",
                bottleneck="memory_bandwidth",
                confidence=0.87,
                explanation="GPU utilization is low (~41%) while memory bandwidth and access patterns stall execution.",
                recommendations=["Investigate memory access patterns", "Reduce unnecessary host-to-device transfers", "Enable fused operations"]
            )
        elif s == DemoScenario.CPU_BOTTLENECK:
            return DiagnoseResponse(
                status="warning",
                bottleneck="cpu_starvation",
                confidence=0.91,
                explanation="CPU utilization is pinned (>90%) causing the GPU to idle waiting for input batches.",
                recommendations=["Optimize data loader workers (num_workers)", "Pre-process data offline", "Leverage GPU-accelerated decoding (e.g. DALI)"]
            )
        elif s == DemoScenario.THERMAL_PROBLEM:
            return DiagnoseResponse(
                status="critical",
                bottleneck="thermal_throttling",
                confidence=0.96,
                explanation="Temperature is exceeding 89?C causing hardware clock throttling and degraded latency.",
                recommendations=["Inspect chassis airflow and cooling fans", "Lower power limit temporarily", "Relocate high-load workloads to cooler nodes"]
            )
        elif s == DemoScenario.VRAM_PRESSURE:
            return DiagnoseResponse(
                status="critical",
                bottleneck="vram_exhaustion",
                confidence=0.94,
                explanation="VRAM allocation exceeds 98%, risking Out-Of-Memory (OOM) fatal crashes.",
                recommendations=["Reduce batch size immediately", "Enable gradient checkpointing", "Offload non-critical tensors to CPU RAM"]
            )

    return DiagnoseResponse(
        status="healthy",
        bottleneck="none",
        confidence=0.95,
        explanation="Phase 1: Deterministic rules engine active in preview mode.",
        recommendations=["Full diagnostic engine will be enabled in Phase 5"]
    )
