import re
import json
import time
import logging
import subprocess
from typing import Optional, Dict, Any

from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

logger = logging.getLogger("GPUPilot.Intel")

# ---------------------------------------------------------------------------
# Windows helpers - queries via built-in PowerShell / WMI / DXGI counters.
# No extra Python packages needed (psutil already installed).
# ---------------------------------------------------------------------------


def _run_ps(cmd: str, timeout: int = 10) -> Optional[str]:
    """Run a PowerShell command, return stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _detect_intel_gpu() -> Optional[Dict[str, Any]]:
    """
    Use WMI Win32_VideoController to find the first Intel GPU.
    Returns dict {name, driver_version, adapter_ram_bytes} or None.
    """
    ps = (
        "Get-WmiObject Win32_VideoController "
        "| Select-Object Name, DriverVersion, AdapterRAM "
        "| ConvertTo-Json -Compress"
    )
    raw = _run_ps(ps)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        for item in data:
            name = item.get("Name", "")
            if "intel" in name.lower():
                return {
                    "name": name,
                    "driver_version": item.get("DriverVersion"),
                    "adapter_ram_bytes": item.get("AdapterRAM") or 0,
                }
    except Exception:
        pass
    return None


def _get_intel_luid() -> Optional[str]:
    """
    Discover Intel GPU LUID from Windows GPU Engine performance counters.
    Counter instance names embed the LUID, e.g.:
      pid_1234_luid_0x00000000_0x000112cd_phys_0_eng_0_engtype_3d
    We pick the LUID that is NOT associated with NVIDIA adapters.
    """
    counter = r"\GPU Engine(*engtype_3D)\Utilization Percentage"
    ps = (
        f"Get-Counter '{counter}' -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty CounterSamples "
        "| Select-Object InstanceName "
        "| ConvertTo-Json -Compress"
    )
    raw = _run_ps(ps, timeout=12)
    if not raw:
        return None
    try:
        items = json.loads(raw)
        if isinstance(items, dict):
            items = [items]
        luids: set = set()
        for item in items:
            inst = item.get("InstanceName", "")
            m = re.search(r"luid_(0x[0-9a-f]+_0x[0-9a-f]+)", inst, re.IGNORECASE)
            if m:
                luids.add(m.group(1).lower())
        # Exclude known NVIDIA LUIDs (0x11645 = RTX, 0x1167b = PhysX)
        for luid in sorted(luids):
            if "11645" not in luid and "1167b" not in luid:
                return luid
    except Exception:
        pass
    return None


def _query_gpu_utilization(luid: str) -> Optional[float]:
    """Sum 3D-engine utilization across all engines for this adapter LUID."""
    pattern = f"*{luid}*engtype_3d*"
    counter = r"\GPU Engine(*engtype_3D)\Utilization Percentage"
    ps = (
        f"Get-Counter '{counter}' -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty CounterSamples "
        f"| Where-Object {{$_.InstanceName -like '{pattern}'}} "
        "| Measure-Object -Property CookedValue -Sum "
        "| Select-Object -ExpandProperty Sum"
    )
    raw = _run_ps(ps, timeout=12)
    if raw:
        try:
            val = float(raw)
            return round(min(100.0, max(0.0, val)), 1)
        except Exception:
            pass
    return None


def _query_memory(luid: str) -> Dict[str, Optional[float]]:
    """Query adapter-level dedicated memory used and total committed (GB)."""
    result: Dict[str, Optional[float]] = {"used_gb": None, "total_gb": None}
    lf = f"*{luid}*"

    counter_u = r"\GPU Adapter Memory(*)\Dedicated Usage"
    ps_u = (
        f"Get-Counter '{counter_u}' -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty CounterSamples "
        f"| Where-Object {{$_.InstanceName -like '{lf}' -and $_.InstanceName -notlike '*pid*'}} "
        "| Select-Object -ExpandProperty CookedValue"
    )
    raw = _run_ps(ps_u, timeout=12)
    if raw:
        try:
            result["used_gb"] = round(float(raw) / (1024 ** 3), 3)
        except Exception:
            pass

    counter_t = r"\GPU Adapter Memory(*)\Total Committed"
    ps_t = (
        f"Get-Counter '{counter_t}' -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty CounterSamples "
        f"| Where-Object {{$_.InstanceName -like '{lf}' -and $_.InstanceName -notlike '*pid*'}} "
        "| Select-Object -ExpandProperty CookedValue"
    )
    raw = _run_ps(ps_t, timeout=12)
    if raw:
        try:
            result["total_gb"] = round(float(raw) / (1024 ** 3), 3)
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------


class IntelProvider(GPUProvider):
    """
    Intel GPU Provider for Windows.

    Uses:
    - WMI Win32_VideoController   -> GPU name, driver version, adapter RAM
    - Windows DXGI GPU Perf Counters -> live utilisation & memory metrics

    Supports: Intel UHD Graphics, Iris Xe, Intel Arc (iGPU & dGPU).
    Requires no extra Python packages (psutil already present).

    Metrics not exposed by Windows DXGI counters (returned as null):
      temperature, power_usage, fan_speed, gpu_clock, memory_clock.
    """

    def __init__(self) -> None:
        self._available: bool = False
        self._name: str = "Intel Graphics"
        self._driver_version: Optional[str] = None
        self._adapter_ram_bytes: int = 0
        self._luid: Optional[str] = None
        self._init_intel()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_intel(self) -> None:
        hw = _detect_intel_gpu()
        if hw is None:
            logger.debug("IntelProvider: no Intel GPU found via WMI.")
            return

        self._name = hw["name"]
        self._driver_version = hw.get("driver_version")
        self._adapter_ram_bytes = hw.get("adapter_ram_bytes", 0)
        self._luid = _get_intel_luid()

        if self._luid:
            logger.info(
                "IntelProvider ready: %s | Driver %s | LUID %s",
                self._name, self._driver_version, self._luid,
            )
        else:
            logger.warning(
                "IntelProvider: '%s' detected but LUID discovery failed "
                "— utilisation/memory metrics unavailable.",
                self._name,
            )

        self._available = True

    # ------------------------------------------------------------------
    # GPUProvider interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        if not self._available:
            return GPUInfo(
                vendor="Intel",
                name="Intel GPU (Unavailable)",
                driver_version=None,
                provider_type="IntelProvider",
                available=False,
                is_demo=False,
                details={"error": "No Intel GPU detected via WMI"},
            )

        shared_gb = (
            round(self._adapter_ram_bytes / (1024 ** 3), 2)
            if self._adapter_ram_bytes else None
        )
        return GPUInfo(
            vendor="Intel",
            name=self._name,
            driver_version=self._driver_version,
            provider_type="IntelProvider",
            available=True,
            is_demo=False,
            details={
                "luid": self._luid,
                "adapter_shared_ram_gb": shared_gb,
                "monitoring_api": "Windows DXGI GPU Performance Counters",
                "note": (
                    "Intel iGPU uses shared system RAM. "
                    "Temperature, power, and clock metrics are not "
                    "available via Windows DXGI counters."
                ),
            },
        )

    def get_metrics(self) -> GPUMetrics:
        if not self._available:
            raise RuntimeError("Intel GPU is not available on this system.")

        # GPU engine utilisation
        gpu_util: Optional[float] = None
        if self._luid:
            gpu_util = _query_gpu_utilization(self._luid)

        # Memory
        mem_used: Optional[float] = None
        mem_total: Optional[float] = None
        mem_util: Optional[float] = None
        if self._luid:
            m = _query_memory(self._luid)
            mem_used = m.get("used_gb")
            mem_total = m.get("total_gb")
            if mem_used is not None and mem_total and mem_total > 0:
                mem_util = round((mem_used / mem_total) * 100.0, 1)

        # CPU utilisation
        cpu_util: Optional[float] = None
        try:
            import psutil
            cpu_util = round(float(psutil.cpu_percent(interval=None)), 1)
        except Exception:
            pass

        return GPUMetrics(
            vendor="Intel",
            name=self._name,
            gpu_utilization=gpu_util,
            memory_used=mem_used,
            memory_total=mem_total,
            memory_utilization=mem_util,
            temperature=None,
            power_usage=None,
            power_limit=None,
            fan_speed=None,
            gpu_clock=None,
            memory_clock=None,
            cpu_utilization=cpu_util,
            latency=None,
            throughput=None,
            timestamp=time.time(),
        )
