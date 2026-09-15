from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

class IntelProvider(GPUProvider):
    """
    Intel GPU Provider.
    Phase 1: Stub that checks for Intel GPU monitoring availability.
    Full monitoring implementation will be delivered in Phase 4.
    """

    def __init__(self):
        self._available = False

    def is_available(self) -> bool:
        return False

    def get_info(self) -> GPUInfo:
        return GPUInfo(
            vendor="Intel",
            name="Intel GPU (Unavailable)",
            provider_type="IntelProvider",
            available=False,
            is_demo=False
        )

    def get_metrics(self) -> GPUMetrics:
        raise NotImplementedError("Intel metric collection will be enabled in Phase 4.")
