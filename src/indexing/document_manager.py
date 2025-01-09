"""Facade for document management operations.

This module provides a facade for document management operations, offering a
simplified interface for document storage and retrieval while maintaining
backward compatibility with existing code.

Features:
1. Document Storage:
   - Document creation and updates
   - Batch operations support
   - Caching integration
   - Error handling

2. Backward Compatibility:
   - Legacy interface support
   - API consistency
   - Migration support
   - Version handling

3. Resource Management:
   - Connection pooling
   - Cache management
   - Batch size control
   - Resource cleanup

Usage:
    ```python
    import weaviate
    from src.utils.cache_manager import CacheManager
    from src.indexing.document_manager import DocumentManager

    # Initialize client and cache
    client = weaviate.Client("http://localhost:8080")
    cache = CacheManager(host="localhost", port=6379)

    # Create document manager
    doc_manager = DocumentManager(
        client=client,
        class_name="Document",
        batch_size=100,
        cache_manager=cache
    )
    ```

Note:
    - Implements facade pattern
    - Handles connection management
    - Provides error handling
    - Supports caching operations
"""

from typing import Optional

import weaviate

from src.utils.cache_manager import CacheManager

from .document import DocumentStorage


class DocumentManager(DocumentStorage):
    """Backward-compatible facade for document operations.

    This class provides a simplified interface for document management while
    maintaining compatibility with existing code. It handles document storage,
    retrieval, and caching operations.

    Attributes:
        client: Weaviate client instance for database operations
        class_name: Name of the document class in Weaviate
        batch_size: Size of batches for bulk operations
        cache_manager: Optional cache manager for performance optimization
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        batch_size: int = 100,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize document manager.

        Args:
            client: Weaviate client instance for database operations
            class_name: Name of the document class in Weaviate
            batch_size: Size of batches for bulk operations (default: 100)
            cache_manager: Optional cache manager for performance optimization

        Example:
            >>> client = weaviate.Client("http://localhost:8080")
            >>> doc_manager = DocumentManager(
            ...     client=client,
            ...     class_name="Document",
            ...     batch_size=100
            ... )
        """
        super().__init__(client, class_name, batch_size, cache_manager)
