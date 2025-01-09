"""Caching module for text summarization.

This module provides caching functionality for text summarization results,
enabling efficient storage and retrieval of processed documents. It includes:

1. Caching Features:
   - Redis integration
   - Key management
   - TTL support
   - Error handling

2. Decorators:
   - Cache wrapping
   - Retry logic
   - Type preservation
   - Resource cleanup

3. Integration:
   - Pipeline support
   - Configuration
   - Monitoring
   - Cleanup

Usage:
    ```python
    from src.utils.summarizer.caching import with_cache
    from src.utils.summarizer.config import CacheConfig

    class Processor:
        def __init__(self):
            self.cache_config = CacheConfig(enabled=True)

        @with_cache(key_prefix="doc")
        def process_document(self, doc):
            # Process document
            return result
    ```

Note:
    - Requires Redis server
    - Handles serialization
    - Supports retry logic
    - Provides fallback
"""

from .decorators import with_cache

__all__ = ["with_cache"]
