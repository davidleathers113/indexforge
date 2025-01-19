"""Decorators for embedding service functionality.

This module provides decorators for common embedding service operations
like metadata tracking and state validation.
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from src.core import BaseService
from src.ml.processing.models.service import ServiceNotInitializedError

T = TypeVar("T")


def track_metadata(
    metadata_key: str,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for tracking operation metadata.

    Args:
        metadata_key: Key to store metadata under

    Returns:
        Decorated function that tracks metadata
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(
            self: BaseService,
            *args: Any,
            metadata: Optional[dict[str, Any]] = None,
            **kwargs: Any,
        ) -> T:
            result = func(self, *args, metadata=metadata, **kwargs)
            if metadata:
                self.add_metadata(metadata_key, metadata)
            return result

        return wrapper

    return decorator


def validate_service_state(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to validate service state before operation.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that validates service state
    """

    @wraps(func)
    def wrapper(self: BaseService, *args: Any, **kwargs: Any) -> T:
        if not getattr(self, "_initialized", False):
            raise ServiceNotInitializedError("Service not initialized")
        self._check_running()  # type: ignore
        return func(self, *args, **kwargs)

    return wrapper
