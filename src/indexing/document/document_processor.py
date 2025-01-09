"""Document preparation and validation operations module.

This module provides functionality for processing, validating, and managing document
operations including preparation for indexing, validation of document structure,
merging updates, and computing document hashes for deduplication.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple


class DocumentProcessor:
    """Handles document preparation, validation, and processing operations.

    This class provides methods for preparing documents for indexing, validating
    document structure, merging document updates, and computing document hashes
    for deduplication purposes.

    Attributes:
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(self):
        """Initialize document processor with logging configuration."""
        self.logger = logging.getLogger(__name__)

    def prepare_document(self, doc: Dict) -> Tuple[Dict, List[float]]:
        """Prepare document properties and vector for indexing.

        Processes a raw document by extracting and organizing its properties
        and embedding vector for indexing operations.

        Args:
            doc: Raw document dictionary containing:
                - content: Document content
                - embeddings: Embedding vectors and metadata
                - metadata: Document metadata
                - relationships: Document relationships

        Returns:
            Tuple[Dict, List[float]]: A tuple containing:
                - Dict: Processed document properties
                - List[float]: Document embedding vector

        Example:
            ```python
            doc = {
                "content": {"body": "text"},
                "embeddings": {"body": [0.1, 0.2], "model": "v1"},
                "metadata": {"title": "Doc"},
                "relationships": {"parent_id": "123"}
            }
            properties, vector = processor.prepare_document(doc)
            ```
        """
        vector = doc["embeddings"]["body"]
        properties = {
            "content": doc["content"],
            "metadata": doc["metadata"],
            "embedding_model": doc["embeddings"]["model"],
            "embedding_version": doc["embeddings"]["version"],
            "parent_id": doc["relationships"]["parent_id"],
            "chunk_ids": doc["relationships"]["chunk_ids"],
            "last_updated": datetime.utcnow().isoformat(),
        }
        return properties, vector

    def validate_document(self, doc: Dict) -> bool:
        """Validate document structure and required fields.

        Checks if the document contains all required fields and validates
        the presence of essential components like embedding vectors.

        Args:
            doc: Document dictionary to validate containing:
                - content: Document content
                - embeddings: Embedding vectors and metadata
                - metadata: Document metadata
                - relationships: Document relationships

        Returns:
            bool: True if document is valid, False otherwise.

        Example:
            ```python
            doc = {
                "content": {"body": "text"},
                "embeddings": {"body": [0.1, 0.2]},
                "metadata": {"title": "Doc"},
                "relationships": {}
            }
            is_valid = processor.validate_document(doc)
            ```
        """
        required_fields = {"content", "embeddings", "metadata", "relationships"}

        if not all(field in doc for field in required_fields):
            self.logger.warning(
                f"Missing required fields in document: {doc.get('metadata', {}).get('title')}"
            )
            return False

        if "body" not in doc["embeddings"]:
            self.logger.warning("Missing embedding vector")
            return False

        return True

    def merge_document_updates(self, existing: Dict, updates: Dict) -> Dict:
        """Merge updates into existing document properties.

        Creates a new document dictionary by merging update properties into
        existing document properties, updating the last_updated timestamp.

        Args:
            existing: Existing document properties dictionary.
            updates: New properties dictionary to merge into existing document.

        Returns:
            Dict: Merged document properties with updated timestamp.

        Example:
            ```python
            existing = {"title": "Old Title", "content": "Old content"}
            updates = {"title": "New Title"}
            merged = processor.merge_document_updates(existing, updates)
            ```
        """
        merged = existing.copy()
        merged.update(updates)
        merged["last_updated"] = datetime.utcnow().isoformat()
        return merged

    def compute_document_hash(self, doc: Dict) -> str:
        """Compute hash for document deduplication.

        Generates a stable hash of the document's content, metadata, and embeddings
        for deduplication purposes. The hash is computed from a sorted, stable
        string representation of key document components.

        Args:
            doc: Document dictionary containing:
                - content: Document content
                - metadata: Document metadata
                - embeddings: Document embeddings

        Returns:
            str: Stable hash string for the document.

        Raises:
            Exception: If hash computation fails.

        Example:
            ```python
            doc = {
                "content": {"body": "text"},
                "metadata": {"title": "Doc"},
                "embeddings": {"body": [0.1, 0.2]}
            }
            doc_hash = processor.compute_document_hash(doc)
            ```
        """
        try:
            content = []
            for key in sorted(doc.keys()):
                if key in {"content", "metadata", "embeddings"}:
                    content.append(f"{key}:{doc[key]}")
            content_str = "|".join(content)
            return str(hash(content_str))
        except Exception as e:
            self.logger.error(f"Error computing document hash: {str(e)}")
            raise
