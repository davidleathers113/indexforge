"""Storage strategy implementations.

This package provides various storage strategy implementations:
- Base storage protocols and interfaces
- JSON-based storage with atomic operations
- Memory-based storage for testing and caching
"""

from .base import (
    BaseStorage,
    DataCorruptionError,
    DataNotFoundError,
    SerializationStrategy,
    StorageError,
    StorageStrategy,
)
from .json_storage import JsonSerializationError, JsonSerializer, JsonStorage
from .memory_storage import MemoryStorage

__all__ = [
    # Base components
    "BaseStorage",
    "StorageStrategy",
    "SerializationStrategy",
    # Error types
    "StorageError",
    "DataNotFoundError",
    "DataCorruptionError",
    # JSON storage
    "JsonStorage",
    "JsonSerializer",
    "JsonSerializationError",
    # Memory storage
    "MemoryStorage",
]
