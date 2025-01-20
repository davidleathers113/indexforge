"""Storage types package.

This package provides core type definitions for storage operations,
including metrics, strategies, and error types.
"""

from .errors import DataCorruptionError, DataNotFoundError, StorageError
from .metrics import StorageMetrics
from .strategies import SerializationStrategy, StorageStrategy

__all__ = [
    # Metrics
    "StorageMetrics",
    # Strategies
    "StorageStrategy",
    "SerializationStrategy",
    # Errors
    "StorageError",
    "DataNotFoundError",
    "DataCorruptionError",
]
