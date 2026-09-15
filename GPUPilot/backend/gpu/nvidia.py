from gpu.base import GPUProvider
from models.schemas import GPUInfo, GPUMetrics

class NVIDIAProvider(GPUProvider):
    """
    NVIDIA GPU Provider.
    Phase 1: Stub that checks for NVML/pynvml availability.
    Full monitoring implementation will be delivered in Phase 2.
    """

    def __init__(self):
        self._available = False
        self._init_nvml()

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            self._available = device_count > 0
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_info(self) -> GPUInfo:
        if not self._available:
            return GPUInfo(
                vendor="NVIDIA",
                name="NVIDIA GPU (Unavailable)",
                provider_type="NVIDIAProvider",
                available=False,
                is_demo=False
            )
        # Reserved for Phase 2 implementation
        return GPUInfo(
            vendor="NVIDIA",
            name="NVIDIA Device",
            provider_type="NVIDIAProvider",
            available=True,
            is_demo=False
        )

    def get_metrics(self) -> GPUMetrics:
        raise NotImplementedError("NVIDIA metric collection will be enabled in Phase 2.")
