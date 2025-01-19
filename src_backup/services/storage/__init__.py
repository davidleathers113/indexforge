"""Storage service implementations.

This package provides concrete implementations of the core storage interfaces
for document, chunk, and reference storage operations.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Type, TypeVar

from src.core.errors import ServiceInitializationError
from src.core.interfaces.metrics import MetricsProvider, StorageMetrics

from .base import BaseStorageService, BatchConfig


if TYPE_CHECKING:
    from src.core.interfaces.storage import ChunkStorage, DocumentStorage, ReferenceStorage
    from src.core.settings import Settings

T = TypeVar("T", bound=BaseStorageService)

# Service instance cache
_service_cache: dict[str, object] = {}
_metrics_provider: MetricsProvider | None = None
_storage_metrics: StorageMetrics | None = None
_batch_config: BatchConfig | None = None


def configure_storage(
    metrics_provider: MetricsProvider | None = None,
    storage_metrics: StorageMetrics | None = None,
    batch_config: BatchConfig | None = None,
) -> None:
    """Configure global storage service settings.

    Args:
        metrics_provider: Optional metrics provider for detailed metrics
        storage_metrics: Optional storage metrics collector
        batch_config: Optional batch operation configuration
    """
    global _metrics_provider, _storage_metrics, _batch_config
    _metrics_provider = metrics_provider
    _storage_metrics = storage_metrics
    _batch_config = batch_config


def _get_cached_service(
    service_key: str,
    service_class: type[T],
    settings: "Settings",
    **kwargs: Any,
) -> T:
    """Get a cached service instance or create a new one.

    Args:
        service_key: Unique identifier for the service
        service_class: Class of the service to instantiate
        settings: Application settings
        **kwargs: Additional keyword arguments for service initialization

    Returns:
        The cached or newly created service instance
    """
    if service_key not in _service_cache:
        service = service_class(
            settings=settings,
            metrics=_storage_metrics,
            metrics_provider=_metrics_provider,
            batch_config=_batch_config,
            **kwargs,
        )
        _service_cache[service_key] = service
    return _service_cache[service_key]


def clear_service_cache() -> None:
    """Clear all cached service instances.

    This can be useful during testing or when reconfiguring services.
    """
    _service_cache.clear()


def check_service_health() -> tuple[bool, str]:
    """Check the health of all initialized storage services.

    Returns:
        Tuple containing:
            - bool: True if all services are healthy
            - str: Status message or error description
    """
    try:
        for service in _service_cache.values():
            if isinstance(service, BaseStorageService):
                # Check service-specific health
                if hasattr(service, "check_health"):
                    is_healthy, message = service.check_health()
                    if not is_healthy:
                        return False, f"Service unhealthy: {message}"

        return True, "All storage services are healthy"
    except Exception as e:
        return False, f"Health check failed: {e!s}"


def get_document_storage(settings: "Settings") -> "DocumentStorage":
    """Get the document storage service instance.

    Args:
        settings: Application settings

    Returns:
        DocumentStorage: Document storage service instance

    Raises:
        ServiceInitializationError: If service initialization fails
    """
    try:
        from .document_storage import DocumentStorageService

        return _get_cached_service("document_storage", DocumentStorageService, settings)
    except Exception as e:
        raise ServiceInitializationError(f"Failed to initialize document storage: {e}") from e


def get_chunk_storage(settings: "Settings") -> "ChunkStorage":
    """Get the chunk storage service instance.

    Args:
        settings: Application settings

    Returns:
        ChunkStorage: Chunk storage service instance

    Raises:
        ServiceInitializationError: If service initialization fails
    """
    try:
        from .chunk_storage import ChunkStorageService

        return _get_cached_service("chunk_storage", ChunkStorageService, settings)
    except Exception as e:
        raise ServiceInitializationError(f"Failed to initialize chunk storage: {e}") from e


def get_reference_storage(settings: "Settings") -> "ReferenceStorage":
    """Get the reference storage service instance.

    Args:
        settings: Application settings

    Returns:
        ReferenceStorage: Reference storage service instance

    Raises:
        ServiceInitializationError: If service initialization fails
    """
    try:
        from .reference_storage import ReferenceStorageService

        return _get_cached_service("reference_storage", ReferenceStorageService, settings)
    except Exception as e:
        raise ServiceInitializationError(f"Failed to initialize reference storage: {e}") from e


__all__ = [
    "check_service_health",
    "clear_service_cache",
    "configure_storage",
    "get_chunk_storage",
    "get_document_storage",
    "get_reference_storage",
]
