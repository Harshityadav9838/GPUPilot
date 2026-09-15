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
    version: str = "0.1.0"
    active_provider: str
    is_demo: bool

class SetScenarioRequest(BaseModel):
    scenario: DemoScenario

class ScenarioInfo(BaseModel):
    id: DemoScenario
    name: str
    description: str

class DiagnoseResponse(BaseModel):
    status: str
    bottleneck: str
    confidence: float
    explanation: str
    recommendations: List[str]
