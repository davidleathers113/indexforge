"""Document tracking storage implementation.

This package provides storage functionality specifically designed for document tracking:
- Document lineage storage
- Processing history storage
- Metrics and status tracking
- Error and warning logs
"""

from .storage import (
    LineageStorage,
    LineageStorageBase,
    LineageStorageError,
    StorageMetrics,
    StorageStatus,
)

__all__ = [
    # Core storage
    "LineageStorage",
    "LineageStorageBase",
    # Error types
    "LineageStorageError",
    # Metrics and status
    "StorageMetrics",
    "StorageStatus",
]
