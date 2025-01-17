"""Cache service interface.

This module defines the interface for cache services used throughout the system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheService(ABC):
    """Interface for cache services."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: The key to retrieve.

        Returns:
            The cached value if found, None otherwise.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.

        Args:
            key: The key to store.
            value: The value to cache.
            ttl: Optional time-to-live in seconds.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all values from the cache.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the cache service is ready.

        Returns:
            True if the service is ready, False otherwise.
        """
        pass
