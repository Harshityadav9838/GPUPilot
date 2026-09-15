import random
import time
from typing import Dict, Any
from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics, DemoScenario

class DemoProvider(GPUProvider):
    """
    Simulation provider for testing and environments without dedicated GPUs.
    Supports 6 realistic dynamic scenarios with smooth metric fluctuations.
    """

    def __init__(self, initial_scenario: DemoScenario = DemoScenario.HEALTHY):
        self.scenario = initial_scenario
        self.vendor = "Demo"
        self.name = "GPUPilot Virtual Accelerator v100"
        self._step = 0

    def is_available(self) -> bool:
        return True

    def set_scenario(self, scenario: DemoScenario):
        self.scenario = scenario

    def get_info(self) -> GPUInfo:
        return GPUInfo(
            vendor="Demo",
            name=self.name,
            driver_version="Virtual 1.0.0",
            provider_type="DemoProvider",
            is_demo=True,
            available=True,
            details={
                "scenario": self.scenario.value,
                "supported_scenarios": [s.value for s in DemoScenario],
                "virtual_cores": 4096,
                "virtual_vram_gb": 16.0
            }
        )

    def get_metrics(self) -> GPUMetrics:
        self._step += 1
        noise = random.uniform(-1.5, 1.5)

        total_vram = 16.0
        power_limit = 250.0

        if self.scenario == DemoScenario.HEALTHY:
            gpu_util = min(100.0, max(0.0, 68.0 + noise * 2))
            mem_used = round(min(total_vram, max(0.0, 5.2 + noise * 0.15)), 2)
            temp = round(61.0 + noise * 0.8, 1)
            power = round(135.0 + noise * 4, 1)
            fan = round(45.0 + noise, 1)
            gpu_clock = round(1850.0 + noise * 10, 1)
            mem_clock = 7000.0
            cpu_util = round(32.0 + noise * 1.5, 1)
            latency = round(38.0 + noise * 1.2, 1)
            throughput = round(128.0 + noise * 3, 1)

        elif self.scenario == DemoScenario.COMPUTE_BOTTLENECK:
            gpu_util = min(100.0, max(92.0, 97.5 + noise * 1.2))
            mem_used = round(min(total_vram, max(0.0, 6.8 + noise * 0.2)), 2)
            temp = round(77.0 + noise * 0.9, 1)
            power = round(242.0 + noise * 3, 1)
            fan = round(78.0 + noise * 2, 1)
            gpu_clock = round(1920.0 + noise * 5, 1)
            mem_clock = 7000.0
            cpu_util = round(38.0 + noise * 2, 1)
            latency = round(94.0 + noise * 2.5, 1)
            throughput = round(64.0 + noise * 2, 1)

        elif self.scenario == DemoScenario.MEMORY_BOTTLENECK:
            gpu_util = min(100.0, max(20.0, 41.0 + noise * 3))
            mem_used = round(min(total_vram, max(0.0, 14.8 + noise * 0.1)), 2)
            temp = round(64.0 + noise * 0.7, 1)
            power = round(120.0 + noise * 4, 1)
            fan = round(52.0 + noise, 1)
            gpu_clock = round(1550.0 + noise * 15, 1)
            mem_clock = 7000.0
            cpu_util = round(28.0 + noise * 1.5, 1)
            latency = round(145.0 + noise * 5, 1)
            throughput = round(32.0 + noise * 1.5, 1)

        elif self.scenario == DemoScenario.CPU_BOTTLENECK:
            gpu_util = min(100.0, max(10.0, 24.0 + noise * 2))
            mem_used = round(min(total_vram, max(0.0, 4.0 + noise * 0.1)), 2)
            temp = round(48.0 + noise * 0.6, 1)
            power = round(78.0 + noise * 3, 1)
            fan = round(30.0 + noise, 1)
            gpu_clock = round(1350.0 + noise * 20, 1)
            mem_clock = 5000.0
            cpu_util = min(100.0, max(85.0, 94.0 + noise * 1.8))
            latency = round(162.0 + noise * 6, 1)
            throughput = round(24.0 + noise * 1.2, 1)

        elif self.scenario == DemoScenario.THERMAL_PROBLEM:
            gpu_util = min(100.0, max(50.0, 72.0 + noise * 4))
            mem_used = round(min(total_vram, max(0.0, 8.4 + noise * 0.2)), 2)
            temp = round(89.5 + noise * 0.6, 1)
            power = round(210.0 + noise * 5, 1)
            fan = 100.0
            gpu_clock = round(1120.0 + noise * 15, 1)  # Throttled clock
            mem_clock = 6000.0
            cpu_util = round(42.0 + noise * 2, 1)
            latency = round(122.0 + noise * 4, 1)
            throughput = round(48.0 + noise * 2, 1)

        elif self.scenario == DemoScenario.VRAM_PRESSURE:
            gpu_util = min(100.0, max(35.0, 53.0 + noise * 3))
            mem_used = round(min(total_vram, 15.75 + noise * 0.05), 2)
            temp = round(71.0 + noise * 0.8, 1)
            power = round(165.0 + noise * 4, 1)
            fan = round(64.0 + noise * 1.5, 1)
            gpu_clock = round(1680.0 + noise * 15, 1)
            mem_clock = 7000.0
            cpu_util = round(45.0 + noise * 2, 1)
            latency = round(188.0 + noise * 7, 1)
            throughput = round(18.5 + noise * 1.2, 1)

        mem_util = round((mem_used / total_vram) * 100.0, 1)

        return GPUMetrics(
            vendor=self.vendor,
            name=self.name,
            gpu_utilization=round(gpu_util, 1),
            memory_used=mem_used,
            memory_total=total_vram,
            memory_utilization=mem_util,
            temperature=temp,
            power_usage=power,
            power_limit=power_limit,
            fan_speed=fan,
            gpu_clock=gpu_clock,
            memory_clock=mem_clock,
            cpu_utilization=cpu_util,
            latency=latency,
            throughput=throughput,
            timestamp=time.time()
        )
