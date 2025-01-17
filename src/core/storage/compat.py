"""Compatibility layer for storage system migration.

This module provides wrappers around old storage implementations with
deprecation warnings to help users migrate to the new storage system.

Example:
    ```python
    # Old code
    from src.connectors.direct_documentation_indexing.source_tracking import storage_manager

    # New code with compatibility layer
    from src.core.storage.compat import StorageManagerCompat as storage_manager
    ```
"""

import functools
import warnings
from datetime import datetime
from typing import Any, Callable, TypeVar

from src.connectors.direct_documentation_indexing.source_tracking import storage as old_storage
from src.connectors.direct_documentation_indexing.source_tracking import (
    storage_manager as old_storage_manager,
)
from src.core.storage.repositories.documents import DocumentRepository
from src.core.storage.repositories.lineage import LineageRepository
from src.core.storage.strategies.json_storage import JsonStorage

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(message: str) -> Callable[[F], F]:
    """Decorator to mark functions as deprecated."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated. {message}", DeprecationWarning, stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class StorageManagerCompat:
    """Compatibility wrapper for old storage manager."""

    def __init__(self) -> None:
        """Initialize compatibility wrapper."""
        self._old_manager = old_storage_manager.StorageManager()
        self._doc_repo = DocumentRepository(JsonStorage())

    @deprecated(
        "Use DocumentRepository.get_storage_metrics() instead. "
        "This will be removed in version 2.0.0."
    )
    def get_storage_usage(self) -> dict:
        """Get storage usage metrics."""
        return self._old_manager.get_storage_usage()

    @deprecated(
        "Use DocumentRepository.cleanup_old_files() instead. "
        "This will be removed in version 2.0.0."
    )
    def cleanup_old_files(self, max_age_days: int = 30) -> None:
        """Clean up old files."""
        self._old_manager.cleanup_old_files(max_age_days)


class StorageCompat:
    """Compatibility wrapper for old storage implementation."""

    def __init__(self) -> None:
        """Initialize compatibility wrapper."""
        self._old_storage = old_storage.Storage()
        self._doc_repo = DocumentRepository(JsonStorage())
        self._lineage_repo = LineageRepository(JsonStorage())

    @deprecated("Use DocumentRepository.save() instead. " "This will be removed in version 2.0.0.")
    def save_document(self, doc_id: str, data: dict) -> None:
        """Save document data."""
        self._old_storage.save_document(doc_id, data)

    @deprecated("Use DocumentRepository.get() instead. " "This will be removed in version 2.0.0.")
    def get_document(self, doc_id: str) -> dict:
        """Get document data."""
        return self._old_storage.get_document(doc_id)

    @deprecated("Use LineageRepository.save() instead. " "This will be removed in version 2.0.0.")
    def save_lineage(self, doc_id: str, lineage: dict) -> None:
        """Save document lineage."""
        self._old_storage.save_lineage(doc_id, lineage)

    @deprecated("Use LineageRepository.get() instead. " "This will be removed in version 2.0.0.")
    def get_lineage(self, doc_id: str) -> dict:
        """Get document lineage."""
        return self._old_storage.get_lineage(doc_id)

    @deprecated(
        "Use LineageRepository.get_by_time_range() instead. "
        "This will be removed in version 2.0.0."
    )
    def get_lineage_by_time(
        self, start_time: datetime, end_time: datetime | None = None
    ) -> list[dict]:
        """Get lineage records by time range."""
        return self._old_storage.get_lineage_by_time(start_time, end_time)


# Compatibility instances
storage_manager = StorageManagerCompat()
storage = StorageCompat()
