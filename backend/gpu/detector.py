import logging
from typing import Optional
from gpu.base import GPUProvider
from gpu.nvidia import NVIDIAProvider
from gpu.amd import AMDProvider
from gpu.intel import IntelProvider
from gpu.demo import DemoProvider
from models.schemas import DemoScenario

logger = logging.getLogger("GPUPilot.Detector")

_hardware_provider: Optional[GPUProvider] = None
_demo_provider: Optional[DemoProvider] = None
_current_provider: Optional[GPUProvider] = None

def scan_hardware() -> Optional[GPUProvider]:
    """Scan system for supported physical hardware (NVIDIA -> AMD -> Intel)."""
    global _hardware_provider

    # 1. Test NVIDIA
    try:
        nvidia = NVIDIAProvider()
        if nvidia.is_available():
            logger.info("Physical NVIDIA GPU detected via NVML.")
            _hardware_provider = nvidia
            return _hardware_provider
    except Exception as e:
        logger.debug(f"NVIDIA hardware probe failed: {e}")

    # 2. Test AMD
    try:
        amd = AMDProvider()
        if amd.is_available():
            logger.info("Physical AMD GPU detected.")
            _hardware_provider = amd
            return _hardware_provider
    except Exception as e:
        logger.debug(f"AMD hardware probe failed: {e}")

    # 3. Test Intel
    try:
        intel = IntelProvider()
        if intel.is_available():
            logger.info("Physical Intel GPU detected.")
            _hardware_provider = intel
            return _hardware_provider
    except Exception as e:
        logger.debug(f"Intel hardware probe failed: {e}")

    _hardware_provider = None
    return None

def detect_gpu(force_demo: bool = False, default_scenario: DemoScenario = DemoScenario.HEALTHY) -> GPUProvider:
    """
    Detect available GPU hardware and return the active provider adapter.
    Falls back to DemoProvider if no physical hardware is detected or if force_demo=True.
    """
    global _current_provider, _demo_provider, _hardware_provider

    if _demo_provider is None:
        _demo_provider = DemoProvider(initial_scenario=default_scenario)

    if force_demo:
        _current_provider = _demo_provider
        return _current_provider

    hw = scan_hardware()
    if hw is not None and hw.is_available():
        _current_provider = hw
        return _current_provider

    logger.info("No supported physical GPU available. Falling back to DemoProvider.")
    _current_provider = _demo_provider
    return _current_provider

def set_provider_mode(mode: str) -> GPUProvider:
    """Toggle between 'hardware' and 'demo' mode."""
    global _current_provider, _demo_provider, _hardware_provider

    if _demo_provider is None:
        _demo_provider = DemoProvider()

    if mode.lower() == "demo":
        _current_provider = _demo_provider
        return _current_provider
    elif mode.lower() == "hardware":
        if _hardware_provider is None:
            scan_hardware()
        if _hardware_provider is not None and _hardware_provider.is_available():
            _current_provider = _hardware_provider
            return _current_provider
        raise ValueError("No physical GPU hardware is available on this system.")
    else:
        raise ValueError(f"Unknown provider mode: {mode}. Must be 'hardware' or 'demo'.")

def get_active_provider() -> GPUProvider:
    global _current_provider
    if _current_provider is None:
        _current_provider = detect_gpu()
    return _current_provider

def get_demo_provider() -> DemoProvider:
    global _demo_provider
    if _demo_provider is None:
        _demo_provider = DemoProvider()
    return _demo_provider
