"""Document management package for vector storage system.

This package provides comprehensive document management functionality including:
- Document storage and retrieval with vector search capabilities
- Document processing and validation
- Batch operations management for optimal performance
- Cache management for improved access times

The package is built around Weaviate as the vector storage backend and supports
features like document deduplication, batch processing, and cache invalidation.

Example:
    ```python
    from src.indexing.document import (
        DocumentStorage,
        DocumentProcessor,
        BatchManager
    )

    # Initialize components
    processor = DocumentProcessor()
    batch_mgr = BatchManager(client, "Document", batch_size=100)
    storage = DocumentStorage(
        client=client,
        class_name="Document",
        batch_size=100,
        processor=processor,
        batch_manager=batch_mgr
    )

    # Use storage system
    doc_ids = storage.add_documents(documents)
    storage.update_document(doc_id, updates)
    storage.delete_documents([doc_id])
    ```

Components:
    - DocumentStorage: Main interface for document operations
    - DocumentProcessor: Handles document validation and preparation
    - BatchManager: Manages batched operations for performance
"""

from .batch_manager import BatchManager
from .document_processor import DocumentProcessor
from .document_storage import DocumentStorage


__all__ = ["BatchManager", "DocumentProcessor", "DocumentStorage"]
