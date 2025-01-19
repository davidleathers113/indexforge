"""Metrics tracking for embedding operations.

This module provides metrics tracking functionality using decorators
to monitor embedding operations and performance.
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar

from src.core import BaseService

logger = logging.getLogger(__name__)

T = TypeVar("T")


def track_metrics(
    operation: str, include_args: bool = False
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Track metrics for an operation.

    Args:
        operation: Name of the operation to track
        include_args: Whether to include argument values in metrics

    Returns:
        Decorated function that tracks metrics
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self: BaseService, *args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            success = False
            try:
                result = func(self, *args, **kwargs)
                success = True
                return result
            finally:
                duration = time.perf_counter() - start_time
                metrics = {"operation": operation, "duration": duration, "success": success}

                if include_args:
                    # Safely capture argument values
                    arg_values = {f"arg_{i}": str(arg)[:100] for i, arg in enumerate(args)}
                    metrics.update(arg_values)
                    metrics.update({k: str(v)[:100] for k, v in kwargs.items()})

                self.add_metadata(f"metrics_{operation}", metrics)
                logger.info(
                    "Operation metrics: %s completed in %.3fs (success=%s)",
                    operation,
                    duration,
                    success,
                )

        return wrapper

    return decorator


def batch_metrics(
    batch_size_key: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Track metrics for batch operations.

    Args:
        batch_size_key: Optional key to extract batch size from kwargs

    Returns:
        Decorated function that tracks batch metrics
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self: BaseService, *args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            try:
                result = func(self, *args, **kwargs)

                # Calculate batch size
                batch_size = None
                if batch_size_key and batch_size_key in kwargs:
                    batch_size = len(kwargs[batch_size_key])
                elif args and hasattr(args[0], "__len__"):
                    batch_size = len(args[0])

                if batch_size is not None:
                    duration = time.perf_counter() - start_time
                    metrics = {
                        "batch_size": batch_size,
                        "duration": duration,
                        "items_per_second": batch_size / duration,
                    }
                    self.add_metadata("batch_metrics", metrics)
                    logger.info(
                        "Batch metrics: processed %d items in %.3fs (%.1f items/s)",
                        batch_size,
                        duration,
                        batch_size / duration,
                    )

                return result
            except Exception:
                logger.exception("Batch processing failed")
                raise

        return wrapper

    return decorator
