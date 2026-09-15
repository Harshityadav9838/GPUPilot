from abc import ABC, abstractmethod
from models.schemas import GPUMetrics, GPUInfo

class GPUProvider(ABC):
    """
    Vendor-agnostic Base Provider.
    Every GPU backend (NVIDIA, AMD, Intel, Demo) must implement this interface.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this vendor's GPU hardware and driver API are available."""
        pass

    @abstractmethod
    def get_info(self) -> GPUInfo:
        """Return static metadata about the GPU."""
        pass

    @abstractmethod
    def get_metrics(self) -> GPUMetrics:
        """Return real-time standardized metrics."""
        pass
