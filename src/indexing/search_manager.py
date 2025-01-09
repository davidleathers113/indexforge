"""Facade for search operations.

This module provides a facade for search operations, offering a simplified
interface for document search while maintaining backward compatibility with
existing code.

Features:
1. Search Operations:
   - Semantic search
   - Hybrid search
   - Filter queries
   - Result ranking

2. Backward Compatibility:
   - Legacy interface support
   - API consistency
   - Version handling
   - Query compatibility

3. Resource Management:
   - Connection handling
   - Query optimization
   - Result caching
   - Error handling

Usage:
    ```python
    import weaviate
    from src.indexing.search_manager import SearchManager

    # Initialize client
    client = weaviate.Client("http://localhost:8080")

    # Create search manager
    search_manager = SearchManager(
        client=client,
        class_name="Document"
    )

    # Perform search
    results = search_manager.semantic_search(
        query_vector=[0.1, 0.2, 0.3],
        limit=10
    )
    ```

Note:
    - Implements facade pattern
    - Optimizes search performance
    - Provides result ranking
    - Handles search errors
"""

import weaviate

from .search import SearchExecutor


class SearchManager(SearchExecutor):
    """Backward-compatible facade for search operations.

    This class provides a simplified interface for search operations while
    maintaining compatibility with existing code. It handles semantic search,
    hybrid search, and result ranking.

    Attributes:
        client: Weaviate client instance
        class_name: Name of the document class
    """

    def __init__(self, client: weaviate.Client, class_name: str):
        """Initialize search manager.

        Args:
            client: Weaviate client instance for search operations
            class_name: Name of the document class in Weaviate

        Example:
            >>> client = weaviate.Client("http://localhost:8080")
            >>> search_manager = SearchManager(
            ...     client=client,
            ...     class_name="Document"
            ... )
        """
        super().__init__(client, class_name)
