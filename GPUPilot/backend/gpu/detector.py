import logging
from typing import Optional
from gpu.base import GPUProvider
from gpu.nvidia import NVIDIAProvider
from gpu.amd import AMDProvider
from gpu.intel import IntelProvider
from gpu.demo import DemoProvider
from models.schemas import DemoScenario

logger = logging.getLogger("GPUPilot.Detector")

_current_provider: Optional[GPUProvider] = None

def detect_gpu(force_demo: bool = False, default_scenario: DemoScenario = DemoScenario.HEALTHY) -> GPUProvider:
    """
    Detect available GPU hardware and return the corresponding provider adapter.
    Priority order: NVIDIA -> AMD -> Intel -> DemoProvider (fallback).
    """
    global _current_provider

    if force_demo:
        logger.info("Force demo requested. Instantiating DemoProvider.")
        _current_provider = DemoProvider(initial_scenario=default_scenario)
        return _current_provider

    # 1. Test NVIDIA
    try:
        nvidia = NVIDIAProvider()
        if nvidia.is_available():
            logger.info("NVIDIA GPU detected.")
            _current_provider = nvidia
            return _current_provider
    except Exception as e:
        logger.debug(f"NVIDIA detection failed: {e}")

    # 2. Test AMD
    try:
        amd = AMDProvider()
        if amd.is_available():
            logger.info("AMD GPU detected.")
            _current_provider = amd
            return _current_provider
    except Exception as e:
        logger.debug(f"AMD detection failed: {e}")

    # 3. Test Intel
    try:
        intel = IntelProvider()
        if intel.is_available():
            logger.info("Intel GPU detected.")
            _current_provider = intel
            return _current_provider
    except Exception as e:
        logger.debug(f"Intel detection failed: {e}")

    # 4. Fallback to DemoProvider
    logger.info("No dedicated hardware monitoring library available. Falling back to DemoProvider.")
    _current_provider = DemoProvider(initial_scenario=default_scenario)
    return _current_provider

def get_active_provider() -> GPUProvider:
    global _current_provider
    if _current_provider is None:
        _current_provider = detect_gpu()
    return _current_provider
