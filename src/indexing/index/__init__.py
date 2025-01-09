"""Vector indexing package for efficient document storage and retrieval.

This package provides functionality for vector-based document indexing and search
operations. It includes components for configuring and managing vector indices,
with support for efficient similarity search and document retrieval.

Classes:
    VectorIndex: Main class for vector-based document indexing and search
    IndexConfig: Configuration settings for vector index initialization

Example:
    ```python
    from src.indexing.index import VectorIndex, IndexConfig

    # Initialize index with configuration
    config = IndexConfig(
        url="http://localhost:8080",
        class_name="Document"
    )
    index = VectorIndex(config)

    # Index a document
    doc = {
        "content": "Document text",
        "embedding": [0.1, 0.2, 0.3]
    }
    index.add_document(doc)

    # Search for similar documents
    results = index.search(
        query_vector=[0.15, 0.25, 0.35],
        limit=5
    )
    ```
"""

from .index_config import IndexConfig
from .vector_index import VectorIndex

__all__ = ["VectorIndex", "IndexConfig"]
