import logging
import time
from typing import Optional, Dict, Any
from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

logger = logging.getLogger("GPUPilot.AMD")

class AMDProvider(GPUProvider):
    """
    Production AMD GPU Provider using official AMD SMI (System Management Interface) / ROCm.
    Collects live standardized metrics and gracefully handles non-AMD systems and unsupported sensors.
    """

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self._available = False
        self._handle = None
        self._name = "AMD Radeon GPU"
        self._driver_version = "Unknown"
        self._init_amd()

    def _init_amd(self):
        """Safely attempt to initialize AMD SMI."""
        try:
            import amdsmi
            amdsmi.amdsmi_init()
            processors = amdsmi.amdsmi_get_processor_handles()
            if processors and len(processors) > self.device_index:
                self._handle = processors[self.device_index]
                # Try getting device name
                try:
                    raw_name = amdsmi.amdsmi_get_gpu_device_name(self._handle)
                    self._name = str(raw_name).strip()
                except Exception:
                    self._name = "AMD Radeon Device"

                # Try getting driver version
                try:
                    driver_info = amdsmi.amdsmi_get_driver_info()
                    self._driver_version = str(driver_info.get("driver_version", "ROCm / AMD SMI"))
                except Exception:
                    self._driver_version = "ROCm / AMD SMI"

                self._available = True
                logger.info(f"AMD SMI initialized: {self._name} (Driver: {self._driver_version})")
            else:
                self._available = False
        except (ImportError, ModuleNotFoundError):
            logger.debug("AMD SMI Python package (amdsmi) is not installed.")
            self._available = False
        except Exception as e:
            logger.debug(f"AMD SMI initialization failed: {e}")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        if not self._available:
            return GPUInfo(
                vendor="AMD",
                name="AMD GPU (Unavailable)",
                driver_version=None,
                provider_type="AMDProvider",
                available=False,
                is_demo=False,
                details={"error": "AMD hardware or AMD SMI / ROCm driver is not accessible"}
            )

        details: Dict[str, Any] = {
            "device_index": self.device_index,
        }

        try:
            import amdsmi
            vram = amdsmi.amdsmi_get_gpu_vram_usage(self._handle)
            if vram and "vram_total" in vram:
                details["total_vram_gb"] = round(vram["vram_total"] / (1024 ** 3), 2)
        except Exception:
            pass

        return GPUInfo(
            vendor="AMD",
            name=self._name,
            driver_version=self._driver_version,
            provider_type="AMDProvider",
            available=True,
            is_demo=False,
            details=details
        )

    def _safe_query(self, query_fn, default=None):
        """Helper to execute AMD SMI calls and return default (None) if unsupported."""
        try:
            return query_fn()
        except Exception:
            return default

    def get_metrics(self) -> GPUMetrics:
        if not self._available or not self._handle:
            raise RuntimeError("AMD GPU is not available on this system.")

        import amdsmi

        # 1. GPU Engine Utilization
        gpu_util = None
        activity = self._safe_query(lambda: amdsmi.amdsmi_get_gpu_activity(self._handle))
        if activity and isinstance(activity, dict):
            # gfx_activity is the primary core compute engine load
            if "gfx_activity" in activity:
                gpu_util = float(activity["gfx_activity"])
            elif "engine_activity" in activity:
                gpu_util = float(activity["engine_activity"])

        # 2. VRAM Allocation
        mem_used = None
        mem_total = None
        mem_util = None
        vram = self._safe_query(lambda: amdsmi.amdsmi_get_gpu_vram_usage(self._handle))
        if vram and isinstance(vram, dict):
            raw_used = vram.get("vram_used") or vram.get("used")
            raw_total = vram.get("vram_total") or vram.get("total")
            if raw_used is not None and raw_total is not None and raw_total > 0:
                mem_used = round(raw_used / (1024 ** 3), 2)
                mem_total = round(raw_total / (1024 ** 3), 2)
                mem_util = round((mem_used / mem_total) * 100.0, 1)

        # 3. Core Temperature (Edge or Junction)
        temp = None
        try:
            temp_type = getattr(amdsmi, "AmdSmiTemperatureType", None)
            temp_metric = getattr(amdsmi, "AmdSmiTemperatureMetric", None)
            if temp_type and temp_metric:
                temp_val = self._safe_query(
                    lambda: amdsmi.amdsmi_get_temp_metric(self._handle, temp_type.EDGE, temp_metric.CURRENT)
                )
                if temp_val is not None:
                    # In some amdsmi versions, temperature is reported in millidegrees or integer degrees
                    temp = float(temp_val / 1000.0) if temp_val > 1000 else float(temp_val)
        except Exception:
            pass

        # 4. Power Draw & Limit
        power_usage = None
        power_limit = None
        power_info = self._safe_query(lambda: amdsmi.amdsmi_get_power_info(self._handle))
        if power_info and isinstance(power_info, dict):
            cur_pwr = power_info.get("current_socket_power") or power_info.get("average_socket_power")
            pwr_cap = power_info.get("power_limit")
            if cur_pwr is not None:
                power_usage = round(float(cur_pwr), 1) if float(cur_pwr) < 2000 else round(float(cur_pwr) / 1000.0, 1)
            if pwr_cap is not None:
                power_limit = round(float(pwr_cap), 1) if float(pwr_cap) < 2000 else round(float(pwr_cap) / 1000.0, 1)

        # 5. Fan Speed (%)
        fan_speed = None
        fan_val = self._safe_query(lambda: amdsmi.amdsmi_get_gpu_fan_speed(self._handle, 0))
        if fan_val is not None:
            try:
                fan_speed = float(fan_val)
            except Exception:
                pass

        # 6. Clocks (Graphics & Memory MHz)
        gpu_clock = None
        mem_clock = None
        try:
            clk_type = getattr(amdsmi, "AmdSmiClkType", None)
            if clk_type:
                gfx_clk = self._safe_query(lambda: amdsmi.amdsmi_get_clock_info(self._handle, clk_type.GFX))
                if gfx_clk and isinstance(gfx_clk, dict):
                    gpu_clock = float(gfx_clk.get("cur_clk") or gfx_clk.get("clk", 0))
                mem_clk_val = self._safe_query(lambda: amdsmi.amdsmi_get_clock_info(self._handle, clk_type.MEM))
                if mem_clk_val and isinstance(mem_clk_val, dict):
                    mem_clock = float(mem_clk_val.get("cur_clk") or mem_clk_val.get("clk", 0))
        except Exception:
            pass

        # 7. Host CPU Utilization
        cpu_util = None
        try:
            import psutil
            cpu_util = round(float(psutil.cpu_percent(interval=None)), 1)
        except Exception:
            pass

        return GPUMetrics(
            vendor="AMD",
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
            latency=None,
            throughput=None,
            timestamp=time.time()
        )

    def __del__(self):
        try:
            import amdsmi
            amdsmi.amdsmi_shut_down()
        except Exception:
            pass
