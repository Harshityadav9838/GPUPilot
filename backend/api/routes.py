from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from pydantic import BaseModel
from models.schemas import (
    HealthResponse,
    GPUInfo,
    GPUMetrics,
    SetScenarioRequest,
    ScenarioInfo,
    DemoScenario,
    DiagnoseResponse,
    OptimizationPlanResponse,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkStatus,
    AgentChatRequest,
    AgentChatResponse,
    TuningProfile,
    ApplyTuningRequest,
    ApplyTuningResponse,
)
from gpu.detector import get_active_provider, set_provider_mode, get_demo_provider, scan_hardware
from gpu.demo import DemoProvider
from gpu import diagnostics as engine
from gpu import optimizer
from gpu import benchmark
from gpu import agent
from gpu import tuner
from config import settings

router = APIRouter()


class ModeRequest(BaseModel):
    mode: str  # "hardware" or "demo"


@router.get("/health", response_model=HealthResponse)
def get_health():
    provider = get_active_provider()
    info = provider.get_info()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        active_provider=info.provider_type,
        is_demo=info.is_demo,
    )


@router.get("/gpu", response_model=GPUInfo)
def get_gpu():
    return get_active_provider().get_info()


@router.get("/metrics", response_model=GPUMetrics)
def get_metrics():
    provider = get_active_provider()
    try:
        return provider.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {e}")


@router.post("/provider/mode")
def switch_mode(req: ModeRequest):
    try:
        provider = set_provider_mode(req.mode)
        info = provider.get_info()
        return {
            "status": "success",
            "active_mode": req.mode,
            "provider": info.provider_type,
            "is_demo": info.is_demo,
            "gpu_name": info.name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/demo/scenarios", response_model=List[ScenarioInfo])
def list_demo_scenarios():
    return [
        ScenarioInfo(id=DemoScenario.HEALTHY,           name="Healthy Workload",
            description="Optimal balanced utilization (~68%), safe temperature and low latency."),
        ScenarioInfo(id=DemoScenario.COMPUTE_BOTTLENECK, name="Compute Bottleneck",
            description="GPU utilization pinned near 98%, high power draw, compute-bound kernels."),
        ScenarioInfo(id=DemoScenario.MEMORY_BOTTLENECK,  name="Memory Bottleneck",
            description="Low GPU utilization (~41%) with high memory pressure and transfer stalls."),
        ScenarioInfo(id=DemoScenario.CPU_BOTTLENECK,     name="CPU Starvation Bottleneck",
            description="Host CPU pinned >90% while GPU waits starved with low utilization (~24%)."),
        ScenarioInfo(id=DemoScenario.THERMAL_PROBLEM,    name="Thermal Throttling",
            description="Critical temperatures (~90 C), max fan speed (100%), reduced core clock."),
        ScenarioInfo(id=DemoScenario.VRAM_PRESSURE,      name="VRAM OOM Pressure",
            description="VRAM usage >95% causing thrashing, high latency spikes, low throughput."),
    ]


@router.post("/demo/scenario")
def set_demo_scenario(req: SetScenarioRequest):
    provider = get_active_provider()
    if not isinstance(provider, DemoProvider):
        provider = set_provider_mode("demo")
    if isinstance(provider, DemoProvider):
        provider.set_scenario(req.scenario)
        return {"status": "success", "active_scenario": req.scenario.value, "is_demo": True}
    raise HTTPException(status_code=400, detail="Unable to switch to Demo Mode.")


@router.get("/diagnose", response_model=DiagnoseResponse)
def get_diagnosis():
    provider = get_active_provider()
    try:
        metrics = provider.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")

    result = engine.analyse(metrics)
    return DiagnoseResponse(
        status=result.status,
        bottleneck=result.bottleneck,
        confidence=result.confidence,
        severity=result.severity,
        title=result.title,
        explanation=result.explanation,
        recommendations=result.recommendations,
        metrics_snapshot=result.metrics_snapshot,
    )


@router.get("/optimize", response_model=OptimizationPlanResponse)
def get_optimization_plan():
    provider = get_active_provider()
    try:
        metrics = provider.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics for optimization: {e}")

    return optimizer.generate_plan(metrics)


# Phase 7: Benchmarking Endpoints
@router.post("/benchmark/run", response_model=BenchmarkStatus)
def run_benchmark(req: BenchmarkRequest, background_tasks: BackgroundTasks):
    status = benchmark.get_benchmark_status()
    if status.is_running:
        raise HTTPException(status_code=409, detail="A benchmark is currently running. Please wait for completion.")

    provider = get_active_provider()
    background_tasks.add_task(benchmark.execute_benchmark, req, provider.get_metrics)
    return benchmark.get_benchmark_status()


@router.get("/benchmark/status", response_model=BenchmarkStatus)
def get_benchmark_status():
    return benchmark.get_benchmark_status()


@router.get("/benchmark/history", response_model=List[BenchmarkResult])
def get_benchmark_history():
    return benchmark.get_benchmark_history()


# Phase 9: AI Agent / Workload Explainer Endpoints
@router.post("/agent/chat", response_model=AgentChatResponse)
def chat_with_agent(req: AgentChatRequest):
    provider = get_active_provider()
    try:
        metrics = provider.get_metrics()
    except Exception:
        metrics = GPUMetrics(vendor="Unknown", name="Accelerator")
    return agent.explain_state(metrics, req.prompt, api_key=req.api_key, model_name=req.model or "gemini-1.5-flash")



# Phase 10: Autonomous Tuning Engine Endpoints
@router.get("/tuner/profiles", response_model=List[TuningProfile])
def list_tuning_profiles():
    return tuner.get_profiles()


@router.post("/tuner/apply", response_model=ApplyTuningResponse)
def apply_tuning_profile(req: ApplyTuningRequest):
    try:
        return tuner.apply_profile(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
