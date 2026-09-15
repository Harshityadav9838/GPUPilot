import logging
import time
from typing import Optional, Dict, Any
from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

logger = logging.getLogger("GPUPilot.NVIDIA")

class NVIDIAProvider(GPUProvider):
    """
    Production NVIDIA GPU Provider using official NVIDIA Management Library (NVML).
    Collects live standardized metrics and gracefully handles unsupported sensors.
    """

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self._available = False
        self._handle = None
        self._name = "NVIDIA Device"
        self._driver_version = "Unknown"
        self._init_nvml()

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > self.device_index:
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
                raw_name = pynvml.nvmlDeviceGetName(self._handle)
                # In some pynvml versions, name might be bytes
                self._name = raw_name.decode("utf-8") if isinstance(raw_name, bytes) else str(raw_name)
                raw_driver = pynvml.nvmlSystemGetDriverVersion()
                self._driver_version = raw_driver.decode("utf-8") if isinstance(raw_driver, bytes) else str(raw_driver)
                self._available = True
                logger.info(f"NVIDIA NVML initialized: {self._name} (Driver: {self._driver_version})")
            else:
                logger.warning(f"NVML initialized but device index {self.device_index} not found (count: {device_count})")
                self._available = False
        except Exception as e:
            logger.debug(f"NVIDIA NVML initialization unavailable: {e}")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        if not self._available:
            return GPUInfo(
                vendor="NVIDIA",
                name="NVIDIA GPU (Unavailable)",
                driver_version=None,
                provider_type="NVIDIAProvider",
                available=False,
                is_demo=False,
                details={"error": "NVIDIA hardware or NVML driver is not accessible"}
            )

        details: Dict[str, Any] = {
            "device_index": self.device_index,
        }

        try:
            import pynvml
            mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            details["total_vram_gb"] = round(mem.total / (1024 ** 3), 2)
        except Exception:
            pass

        return GPUInfo(
            vendor="NVIDIA",
            name=self._name,
            driver_version=self._driver_version,
            provider_type="NVIDIAProvider",
            available=True,
            is_demo=False,
            details=details
        )

    def _safe_query(self, query_fn, default=None):
        """Helper to safely execute NVML calls and return default (None) if unsupported."""
        try:
            return query_fn()
        except Exception:
            return default

    def get_metrics(self) -> GPUMetrics:
        if not self._available or not self._handle:
            raise RuntimeError("NVIDIA GPU is not available on this system.")

        import pynvml

        # 1. Core and Memory Utilization
        util = self._safe_query(lambda: pynvml.nvmlDeviceGetUtilizationRates(self._handle))
        gpu_util = float(util.gpu) if util is not None else None

        # 2. VRAM
        mem = self._safe_query(lambda: pynvml.nvmlDeviceGetMemoryInfo(self._handle))
        if mem is not None:
            mem_used = round(mem.used / (1024 ** 3), 2)
            mem_total = round(mem.total / (1024 ** 3), 2)
            mem_util = round((mem.used / mem.total) * 100.0, 1) if mem.total > 0 else None
        else:
            mem_used = None
            mem_total = None
            mem_util = None

        # 3. Temperature
        temp = self._safe_query(
            lambda: float(pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU))
        )

        # 4. Power Draw and Limit (NVML reports milliwatts; convert to Watts)
        power_mw = self._safe_query(lambda: pynvml.nvmlDeviceGetPowerUsage(self._handle))
        power_usage = round(power_mw / 1000.0, 1) if power_mw is not None else None

        power_limit_mw = self._safe_query(lambda: pynvml.nvmlDeviceGetEnforcedPowerLimit(self._handle))
        power_limit = round(power_limit_mw / 1000.0, 1) if power_limit_mw is not None else None

        # 5. Fan Speed (Returns None if unsupported by hardware, e.g. laptop GPUs)
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
            latency=None,       # Specific to active inference workloads
            throughput=None,    # Specific to active inference workloads
            timestamp=time.time()
        )

    def __del__(self):
        try:
            import pynvml
            pynvml.nvmlShutdown()
        except Exception:
            pass
