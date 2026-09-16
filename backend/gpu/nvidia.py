# Production NVIDIA GPU Provider using official NVML (pynvml)
import time
import logging
from typing import Optional, Callable, Any
from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

logger = logging.getLogger("GPUPilot.NVIDIA")


class NVIDIAProvider(GPUProvider):
    def __init__(self, device_index: int = 0):
        self._device_index = device_index
        self._handle = None
        self._available = False
        self._name = "Unknown NVIDIA GPU"
        self._driver_version = "Unknown"
        self._init_nvml()

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(self._device_index)
                raw_name = pynvml.nvmlDeviceGetName(self._handle)
                self._name = raw_name.decode("utf-8") if isinstance(raw_name, bytes) else str(raw_name)
                raw_driver = pynvml.nvmlSystemGetDriverVersion()
                self._driver_version = raw_driver.decode("utf-8") if isinstance(raw_driver, bytes) else str(raw_driver)
                self._available = True
                logger.info(f"NVIDIA NVML initialized: {self._name} (Driver: {self._driver_version})")
            else:
                logger.warning("NVML initialized but 0 devices found.")
                self._available = False
        except Exception as e:
            logger.warning(f"NVML initialization failed: {e}. NVIDIA Provider disabled.")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        if not self._available:
            return GPUInfo(
                vendor="NVIDIA",
                name="NVIDIA GPU (Unavailable)",
                provider_type="NVIDIAProvider",
                is_demo=False,
                available=False,
            )
        return GPUInfo(
            vendor="NVIDIA",
            name=self._name,
            driver_version=self._driver_version,
            provider_type="NVIDIAProvider",
            is_demo=False,
            available=True,
            details={
                "device_index": self._device_index,
                "nvml_loaded": True,
            }
        )

    def _safe_query(self, fn: Callable[[], Any]) -> Optional[Any]:
        try:
            return fn()
        except Exception:
            return None

    def get_metrics(self) -> GPUMetrics:
        if not self._available or self._handle is None:
            raise RuntimeError("NVIDIA Hardware is not available on this host.")

        import pynvml

        # 1. GPU Core Utilization %
        rates = self._safe_query(lambda: pynvml.nvmlDeviceGetUtilizationRates(self._handle))
        gpu_util = float(rates.gpu) if rates is not None else None

        # 2. Memory Utilization and GB
        mem_info = self._safe_query(lambda: pynvml.nvmlDeviceGetMemoryInfo(self._handle))
        if mem_info is not None:
            mem_total = round(mem_info.total / (1024**3), 2)
            mem_used = round(mem_info.used / (1024**3), 2)
            mem_util = round((mem_info.used / mem_info.total) * 100.0, 1)
        else:
            mem_total, mem_used, mem_util = None, None, None

        # 3. Core Temperature (Celsius)
        temp = self._safe_query(
            lambda: float(pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU))
        )

        # 4. Power Draw and Limit (Watts)
        power_mw = self._safe_query(lambda: pynvml.nvmlDeviceGetPowerUsage(self._handle))
        power_usage = round(power_mw / 1000.0, 1) if power_mw is not None else None

        power_limit_mw = self._safe_query(lambda: pynvml.nvmlDeviceGetEnforcedPowerLimit(self._handle))
        power_limit = round(power_limit_mw / 1000.0, 1) if power_limit_mw is not None else None

        # 5. Fan Speed
        fan_speed = self._safe_query(lambda: float(pynvml.nvmlDeviceGetFanSpeed(self._handle)))

        # 6. Core & Memory Clocks
        gpu_clock = self._safe_query(
            lambda: float(pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_GRAPHICS))
        )
        mem_clock = self._safe_query(
            lambda: float(pynvml.nvmlDeviceGetClockInfo(self._handle, pynvml.NVML_CLOCK_MEM))
        )

        # 7. Host CPU Utilization
        cpu_util = None
        try:
            import psutil
            cpu_util = round(float(psutil.cpu_percent(interval=None)), 1)
        except Exception:
            pass

        # 8. Dynamic Compute Throughput Estimate (GFLOPS)
        # Formula: 2 * CUDA Cores (~2048 for RTX 3050 Laptop) * Clock (GHz) * (utilization % / 100)
        throughput_val = None
        if gpu_clock and gpu_util is not None:
            if gpu_util > 0:
                # Active estimated compute throughput in GFLOPS
                gflops = round(2 * 2048 * (gpu_clock / 1000.0) * (gpu_util / 100.0) / 10.0, 1)
                throughput_val = max(1.0, gflops)
            else:
                throughput_val = 0.0

        return GPUMetrics(
            vendor="NVIDIA",
            name=self._name,
            gpu_utilization=gpu_util,
            memory_used=mem_used,
            memory_total=mem_total,
            memory_utilization=mem_util,
            temperature=temp,
            power_usage=power_usage,
            power_limit=power_limit,
            fan_speed=fan_speed,
            gpu_clock=gpu_clock,
            memory_clock=mem_clock,
            cpu_utilization=cpu_util,
            latency=round(1000.0 / max(30.0, (gpu_util * 0.9)), 1) if gpu_util and gpu_util > 5 else None,
            throughput=throughput_val,
            timestamp=time.time()
        )

    def __del__(self):
        try:
            import pynvml
            pynvml.nvmlShutdown()
        except Exception:
            pass
