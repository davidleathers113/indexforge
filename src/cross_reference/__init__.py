"""
Cross-reference management for document chunks.

This package provides functionality for managing and analyzing relationships
between document chunks, including sequential ordering, semantic similarity,
and topic-based clustering.

Example:
    ```python
    from cross_reference import CrossReferenceManager, ReferenceType
    import numpy as np

    # Initialize manager
    manager = CrossReferenceManager(
        similarity_threshold=0.8,
        max_semantic_refs=3,
        n_topics=5
    )

    # Add document chunks
    chunk_ids = ["chunk1", "chunk2", "chunk3"]
    embeddings = np.random.rand(3, 128)  # Example embeddings
    for chunk_id, embedding in zip(chunk_ids, embeddings):
        manager.add_chunk(chunk_id, embedding)

    # Establish references
    manager.establish_sequential_references(chunk_ids)
    manager.establish_semantic_references()
    manager.establish_topic_references()

    # Get references for a chunk
    refs = manager.get_references("chunk1")
    print(f"References: {refs}")
    ```
"""

from .cross_reference_manager import CrossReferenceManager
from .models import ChunkReference, ReferenceType


__all__ = ["ChunkReference", "CrossReferenceManager", "ReferenceType"]
