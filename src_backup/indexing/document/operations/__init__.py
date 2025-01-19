"""Document operations package for storage system management.

This package provides core document operation functionality for the storage system,
including:
- Document addition with batching and deduplication
- Document deletion with cache invalidation
- Document updates with vector management

The operations are designed to work with Weaviate as the backend storage system
and include comprehensive logging, error handling, and cache management.

Example:
    ```python
    from src.indexing.document.operations import (
        DocumentAddition,
        DocumentDeletion,
        DocumentUpdate
    )

    # Initialize operations
    adder = DocumentAddition(client, "Document", batch_size=100)
    deleter = DocumentDeletion(client, "Document")
    updater = DocumentUpdate(client, "Document")

    # Use operations
    doc_ids = adder.add_documents(documents)
    success = deleter.delete_documents(doc_ids)
    updated = updater.update_document(doc_id, updates)
    ```
"""

from src.indexing.document.operations.addition import DocumentAddition
from src.indexing.document.operations.deletion import DocumentDeletion
from src.indexing.document.operations.update import DocumentUpdate


__all__ = ["DocumentAddition", "DocumentDeletion", "DocumentUpdate"]
