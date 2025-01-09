"""Search operations package for vector-based document retrieval.

This package provides functionality for executing semantic searches over indexed
documents and handling search results. It supports various search operations
including similarity search, hybrid search (combining semantic and keyword search),
and filtered searches.

Classes:
    SearchExecutor: Class for executing various types of document searches
    SearchResult: Class representing search results with metadata and scores

Example:
    ```python
    from src.indexing.search import SearchExecutor, SearchResult

    # Initialize search executor
    executor = SearchExecutor(vector_index)

    # Perform semantic search
    results = executor.semantic_search(
        query="machine learning concepts",
        limit=5,
        min_score=0.7
    )

    # Process search results
    for result in results:
        print(f"Document: {result.document_id}")
        print(f"Score: {result.score}")
        print(f"Content: {result.content}")
        print(f"Metadata: {result.metadata}")

    # Hybrid search with filters
    results = executor.hybrid_search(
        text="machine learning",
        filters={
            "metadata.source": "notion",
            "metadata.category": "technical"
        }
    )
    ```

Note:
    Search operations are optimized for performance but may be affected by the
    size of the index and the complexity of the search query.
"""

from .search_executor import SearchExecutor
from .search_result import SearchResult

__all__ = ["SearchExecutor", "SearchResult"]
