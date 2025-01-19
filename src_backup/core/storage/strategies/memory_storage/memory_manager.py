"""Memory management for storage.

This module provides memory tracking and limit enforcement for
in-memory storage operations. It handles memory allocation,
deallocation, and limit checking.

Key Features:
    - Memory usage tracking
    - Size estimation
    - Limit enforcement
    - Resource cleanup
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Generic, TypeVar
import weakref

from .exceptions import MemoryLimitExceededError


logger = logging.getLogger(__name__)

T = TypeVar("T")


class MemoryManager(Generic[T]):
    """Memory management for storage operations."""

    def __init__(self, max_size_bytes: int | None = None, max_items: int | None = None) -> None:
        """Initialize memory manager.

        Args:
            max_size_bytes: Maximum total size in bytes (None for unlimited)
            max_items: Maximum number of items (None for unlimited)
        """
        self._max_size_bytes = max_size_bytes
        self._max_items = max_items
        self._total_size = 0
        self._size_lock = threading.Lock()
        self._instance_sizes: weakref.WeakKeyDictionary[object, int] = weakref.WeakKeyDictionary()

    def check_item_limit(self, current_items: int) -> None:
        """Check if operation would exceed item limit.

        Args:
            current_items: Current number of items

        Raises:
            MemoryLimitExceededError: If operation would exceed limit
        """
        if self._max_items is not None and current_items >= self._max_items:
            raise MemoryLimitExceededError(f"Maximum items ({self._max_items}) exceeded")

    def check_size_limit(self, additional_bytes: int) -> None:
        """Check if operation would exceed size limit.

        Args:
            additional_bytes: Additional bytes to be added

        Raises:
            MemoryLimitExceededError: If operation would exceed limit
        """
        if self._max_size_bytes is None:
            return

        with self._size_lock:
            new_total = self._total_size + additional_bytes
            if new_total > self._max_size_bytes:
                raise MemoryLimitExceededError(
                    f"Operation would exceed memory limit of {self._max_size_bytes} bytes"
                )

    def update_usage(self, instance: object, bytes_delta: int) -> None:
        """Update memory usage tracking.

        Args:
            instance: Instance to track memory for
            bytes_delta: Change in bytes (positive or negative)
        """
        with self._size_lock:
            self._total_size += bytes_delta
            current_size = self._instance_sizes.get(instance, 0)
            new_size = current_size + bytes_delta
            self._instance_sizes[instance] = new_size

    def estimate_size(self, data: dict) -> int:
        """Estimate memory size of data.

        Args:
            data: Data to estimate size for

        Returns:
            Estimated size in bytes
        """
        return sys.getsizeof(data)

    def get_usage_stats(self, instance: object) -> dict[str, int]:
        """Get memory usage statistics.

        Args:
            instance: Instance to get stats for

        Returns:
            Dictionary with memory usage statistics
        """
        with self._size_lock:
            return {
                "total_bytes": self._total_size,
                "instance_bytes": self._instance_sizes.get(instance, 0),
                "max_bytes": self._max_size_bytes,
                "max_items": self._max_items,
            }
