import time
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DemoScenario(str, Enum):
    HEALTHY = "healthy"
    COMPUTE_BOTTLENECK = "compute_bottleneck"
    MEMORY_BOTTLENECK = "memory_bottleneck"
    CPU_BOTTLENECK = "cpu_bottleneck"
    THERMAL_PROBLEM = "thermal_problem"
    VRAM_PRESSURE = "vram_pressure"


class GPUMetrics(BaseModel):
    vendor: str
    name: str
    gpu_utilization: Optional[float] = Field(None, description="GPU core utilization % (0-100)")
    memory_used: Optional[float] = Field(None, description="Used VRAM in GB")
    memory_total: Optional[float] = Field(None, description="Total VRAM in GB")
    memory_utilization: Optional[float] = Field(None, description="Memory utilization % (0-100)")
    temperature: Optional[float] = Field(None, description="GPU temperature in Celsius")
    power_usage: Optional[float] = Field(None, description="Current power draw in Watts")
    power_limit: Optional[float] = Field(None, description="Power limit in Watts")
    fan_speed: Optional[float] = Field(None, description="Fan speed % (0-100)")
    gpu_clock: Optional[float] = Field(None, description="GPU core clock in MHz")
    memory_clock: Optional[float] = Field(None, description="Memory clock in MHz")
    cpu_utilization: Optional[float] = Field(None, description="Host CPU utilization % (0-100)")
    latency: Optional[float] = Field(None, description="Average workload latency in ms")
    throughput: Optional[float] = Field(None, description="Workload throughput in req/s")
    timestamp: float = Field(default_factory=time.time)


class GPUInfo(BaseModel):
    vendor: str
    name: str
    driver_version: Optional[str] = None
    provider_type: str
    is_demo: bool = False
    available: bool = True
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    active_provider: str
    is_demo: bool


class SetScenarioRequest(BaseModel):
    scenario: DemoScenario


class ScenarioInfo(BaseModel):
    id: DemoScenario
    name: str
    description: str


class DiagnoseResponse(BaseModel):
    status: str                              # "healthy" | "warning" | "critical"
    bottleneck: str                          # bottleneck type constant
    confidence: float                        # 0.0 - 1.0
    severity: str = "ok"                     # "ok" | "low" | "medium" | "high" | "critical"
    title: str = ""                          # short human-readable label
    explanation: str                         # 1-2 sentence description
    recommendations: List[str]               # ordered action list
    metrics_snapshot: Optional[Dict[str, Any]] = None  # telemetry at diagnosis time


# Phase 6: Optimization Recommendation Engine Models
class OptimizationRecommendation(BaseModel):
    id: str
    category: str
    title: str
    summary: str
    impact: str                              # "Critical" | "High" | "Medium" | "Low"
    estimated_gain: str
    code_snippet: Optional[str] = None
    doc_url: Optional[str] = None


class OptimizationPlanResponse(BaseModel):
    bottleneck: str
    status: str
    severity: str
    recommendations: List[OptimizationRecommendation]


# Phase 7: GPU Benchmarking Suite Models
class BenchmarkTestType(str, Enum):
    COMPUTE = "compute"
    MEMORY = "memory"
    STRESS = "stress"


class BenchmarkRequest(BaseModel):
    test_type: BenchmarkTestType = BenchmarkTestType.COMPUTE
    duration_seconds: int = Field(default=5, ge=3, le=30)


class BenchmarkTelemetryDelta(BaseModel):
    baseline_temp: Optional[float] = None
    peak_temp: Optional[float] = None
    temp_delta: Optional[float] = None
    peak_power: Optional[float] = None
    power_limit: Optional[float] = None
    avg_clock: Optional[float] = None
    peak_gpu_util: Optional[float] = None
    peak_cpu_util: Optional[float] = None


class BenchmarkResult(BaseModel):
    id: str
    test_type: str
    duration_seconds: int
    score: int
    grade: str
    throughput_ops: float
    telemetry: BenchmarkTelemetryDelta
    timestamp: float = Field(default_factory=time.time)
    summary: str


class BenchmarkStatus(BaseModel):
    is_running: bool
    current_test: Optional[str] = None
    elapsed_seconds: float = 0.0
    total_seconds: float = 0.0
    progress_percent: float = 0.0
    latest_result: Optional[BenchmarkResult] = None


# Phase 9: AI Agent / LLM Explainer Models
class AgentChatRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None
    model: Optional[str] = "gemini-1.5-flash"



class AgentChatResponse(BaseModel):
    response: str
    suggested_actions: List[str] = []
    source: str = "GPUPilot Autonomous Agent"


# Phase 10: Autonomous Tuning Engine Models
class TuningProfile(BaseModel):
    id: str
    name: str
    description: str
    target_power_percent: int
    recommended_batch_multiplier: float
    precision_mode: str
    features: List[str]


class ApplyTuningRequest(BaseModel):
    profile_id: str
    dry_run: bool = False


class ApplyTuningResponse(BaseModel):
    status: str
    profile_id: str
    message: str
    applied_settings: Dict[str, Any]
    dry_run: bool
