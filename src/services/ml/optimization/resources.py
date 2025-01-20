"""Resource management for ML services.

This module provides resource management and optimization capabilities
for ML service operations.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import psutil
import torch

from src.core.settings import Settings
from src.services.ml.errors import ResourceError

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits configuration."""

    max_memory_mb: float
    max_gpu_memory_mb: Optional[float] = None
    target_device: str = "cpu"
    fallback_device: str = "cpu"


class ResourceManager:
    """Manages compute resources for ML operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize resource manager.

        Args:
            settings: Application settings
        """
        self.limits = ResourceLimits(
            max_memory_mb=settings.max_memory_mb,
            max_gpu_memory_mb=settings.get("max_gpu_memory_mb"),
            target_device=settings.get("device", "cpu"),
            fallback_device="cpu",
        )
        self._current_device = self._initialize_device()
        logger.info(f"Resource manager initialized with device: {self._current_device}")

    def _initialize_device(self) -> str:
        """Initialize compute device.

        Returns:
            Selected device name
        """
        if self.limits.target_device == "cpu":
            return "cpu"

        if not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            return "cpu"

        try:
            # Test CUDA device
            torch.zeros(1).cuda()
            return self.limits.target_device
        except Exception as e:
            logger.error(f"Failed to initialize CUDA device: {e}")
            return self.limits.fallback_device

    @property
    def device(self) -> str:
        """Get current compute device."""
        return self._current_device

    def check_memory(self, required_mb: float) -> bool:
        """Check if operation fits in memory.

        Args:
            required_mb: Required memory in MB

        Returns:
            True if operation fits in memory
        """
        current_memory = self._get_memory_usage()
        if current_memory + required_mb > self.limits.max_memory_mb:
            return False

        if self._current_device != "cpu" and self.limits.max_gpu_memory_mb:
            gpu_memory = self._get_gpu_memory_usage()
            if gpu_memory + required_mb > self.limits.max_gpu_memory_mb:
                return False

        return True

    def optimize_batch_size(self, initial_size: int, item_size_mb: float) -> int:
        """Calculate optimal batch size based on memory constraints.

        Args:
            initial_size: Requested batch size
            item_size_mb: Size per item in MB

        Returns:
            Optimized batch size
        """
        total_memory = self.limits.max_memory_mb
        if self._current_device != "cpu" and self.limits.max_gpu_memory_mb:
            total_memory = min(total_memory, self.limits.max_gpu_memory_mb)

        available_memory = total_memory - self._get_memory_usage()
        max_items = int(available_memory / item_size_mb)

        return min(initial_size, max_items)

    async def execute_with_resources(self, operation: Callable, required_mb: float) -> Any:
        """Execute operation with resource checking.

        Args:
            operation: Operation to execute
            required_mb: Required memory in MB

        Returns:
            Operation result

        Raises:
            ResourceError: If operation exceeds resource limits
        """
        if not self.check_memory(required_mb):
            raise ResourceError(
                "Insufficient memory",
                details={
                    "required_mb": required_mb,
                    "available_mb": self.limits.max_memory_mb - self._get_memory_usage(),
                },
            )

        try:
            return await operation()
        except Exception as e:
            raise ResourceError("Operation failed", cause=e) from e

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    def _get_gpu_memory_usage(self) -> float:
        """Get current GPU memory usage in MB."""
        if self._current_device == "cpu":
            return 0.0

        try:
            return torch.cuda.memory_allocated() / 1024 / 1024
        except Exception as e:
            logger.error(f"Failed to get GPU memory usage: {e}")
            return 0.0
