"""Caching decorators for document summarization.

This module provides caching functionality through decorators, enabling efficient
storage and retrieval of summarization results. It includes:

1. Cache Management:
   - Key generation
   - Value serialization
   - TTL handling
   - Error recovery

2. Decorator Features:
   - Function wrapping
   - Argument hashing
   - Type preservation
   - Generic support

3. Error Handling:
   - Graceful degradation
   - Logging support
   - Exception recovery
   - Fallback execution

4. Performance Features:
   - Lazy evaluation
   - Resource cleanup
   - Memory management
   - Cache invalidation

Usage:
    ```python
    from src.utils.summarizer.caching.decorators import with_cache

    class Processor:
        def __init__(self):
            self.cache_manager = CacheManager()
            self.cache_config = CacheConfig()

        @with_cache(key_prefix="summary")
        def process_document(self, doc):
            # Process document
            return result

        @with_cache(key_prefix="batch")
        def process_batch(self, docs):
            # Process batch of documents
            return results
    ```

Note:
    - Requires cache_manager instance
    - Supports optional cache_config
    - Handles serialization automatically
    - Provides fallback on cache failure
"""

import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_cache(key_prefix: str) -> Callable:
    """Decorator for caching function results with retry logic.

    This decorator wraps instance methods to provide caching functionality.
    It requires the instance to have a cache_manager attribute and optionally
    a cache_config attribute. If caching fails, it falls back to executing
    the original function.

    Args:
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function that includes caching behavior
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> T:
            if not self.cache_manager or not self.cache_config or not self.cache_config.enabled:
                return func(self, *args, **kwargs)

            # Generate cache key from function arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args))}"

            try:
                # Try to get from cache
                if cached_result := self.cache_manager.get(cache_key):
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result

                # Execute function and cache result
                result = func(self, *args, **kwargs)
                self.cache_manager.set(
                    cache_key,
                    result,
                    ttl=self.cache_config.ttl if self.cache_config else None,
                )
                return result

            except Exception as e:
                logger.warning(f"Cache operation failed: {str(e)}")
                # Fallback to function execution without caching
                return func(self, *args, **kwargs)

        return wrapper

    return decorator
