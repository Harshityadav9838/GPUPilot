from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

class AMDProvider(GPUProvider):
    """
    AMD GPU Provider.
    Phase 1: Stub that checks for AMD SMI availability.
    Full monitoring implementation will be delivered in Phase 3.
    """

    def __init__(self):
        self._available = False
        self._check_amd()

    def _check_amd(self):
        try:
            import amdsmi
            amdsmi.amdsmi_init()
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        return GPUInfo(
            vendor="AMD",
            name="AMD GPU (Unavailable)" if not self._available else "AMD Radeon",
            provider_type="AMDProvider",
            available=self._available,
            is_demo=False
        )

    def get_metrics(self) -> GPUMetrics:
        raise NotImplementedError("AMD metric collection will be enabled in Phase 3.")
