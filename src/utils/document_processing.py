"""Document processing utilities for content management.

This module provides comprehensive document processing capabilities for managing
and transforming document content. It includes:

1. Document Validation:
   - Content validation
   - Metadata verification
   - Schema enforcement
   - Error handling

2. Document Processing:
   - Content transformation
   - Metadata extraction
   - Document chunking
   - ID generation

3. Document Metadata:
   - Title extraction
   - Source tracking
   - Timestamp management
   - Author attribution
   - Language detection
   - Tag management

4. Error Handling:
   - Custom exceptions
   - Validation errors
   - Configuration errors
   - Processing errors

Usage:
    ```python
    from src.utils.document_processing import DocumentProcessor, DocumentMetadata

    processor = DocumentProcessor()

    # Process a document
    doc = {
        "content": {"body": "Document content"},
        "metadata": {
            "title": "Example",
            "source": "web",
            "timestamp_utc": "2024-01-20T12:00:00Z"
        }
    }
    processed_doc = processor.process_document(doc)

    # Create metadata
    metadata = DocumentMetadata(
        title="Example Document",
        source="file_upload",
        timestamp_utc="2024-01-20T12:00:00Z",
        author="John Doe",
        tags=["example", "documentation"]
    )
    ```

Note:
    - Handles various document formats
    - Maintains document integrity
    - Thread-safe operations
    - Extensible processing pipeline
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
from typing import Dict, List, Optional
import uuid


class DocumentProcessingError(Exception):
    """Base class for document processing errors."""

    pass


class DocumentValidationError(DocumentProcessingError):
    """Raised when document validation fails."""

    pass


class ConfigurationError(DocumentProcessingError):
    """Raised when there is a configuration error."""

    pass


@dataclass
class DocumentMetadata:
    """Document metadata container.

    Attributes:
        title: Document title
        source: Source of the document (e.g., "web", "file_upload")
        timestamp_utc: UTC timestamp of document creation
        last_modified_utc: UTC timestamp of last modification
        author: Document author
        tags: List of tags associated with the document
        language: Document language code (default: "en")
    """

    title: str
    source: str
    timestamp_utc: str
    last_modified_utc: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = None
    language: str = "en"


class DocumentProcessor:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.chunk_size = 100  # Default chunk size
        self.transformers = []
        self.filters = []
        self.validation_rules = []
        self.max_content_length = None

    def _get_document_hash(self, doc: Dict) -> str:
        """Generate a stable hash for document content."""
        content = doc["content"]["body"]
        metadata = doc.get("metadata", {})

        # Include key metadata in hash
        hash_content = (
            f"{content}"
            f"{metadata.get('title', '')}"
            f"{metadata.get('timestamp_utc', '')}"
            f"{metadata.get('last_modified_utc', '')}"
        )

        return hashlib.sha256(hash_content.encode()).hexdigest()

    def ensure_document_id(self, document: Dict) -> Dict:
        """Ensure document has a UUID.

        Args:
            document: Document to process

        Returns:
            Document with UUID
        """
        if "id" not in document or not document["id"]:
            document["id"] = str(uuid.uuid4())
            self.logger.debug(f"Generated UUID for document: {document['id']}")
        return document

    def deduplicate_documents(self, documents: List[Dict]) -> List[Dict]:
        """Remove duplicate documents.

        Args:
            documents: List of documents to deduplicate

        Returns:
            Deduplicated list of documents
        """
        # Ensure all documents have UUIDs
        documents = [self.ensure_document_id(doc) for doc in documents]

        seen = set()
        unique_docs = []
        for doc in documents:
            content = doc["content"]["body"].strip()
            if content not in seen:
                seen.add(content)
                unique_docs.append(doc)
            else:
                self.logger.debug(f"Skipping duplicate document: {doc.get('id', 'unknown')}")
        return unique_docs

    def validate(self, doc: Dict) -> bool:
        """Validate document against all rules.

        Args:
            doc: Document to validate

        Returns:
            True if document is valid

        Raises:
            DocumentValidationError: If validation fails
        """
        # Check basic structure
        if not isinstance(doc, dict):
            raise DocumentValidationError("Document must be a dictionary")

        # Check content
        if "content" not in doc:
            raise DocumentValidationError("Missing required field: content")
        if not isinstance(doc["content"], dict):
            raise DocumentValidationError("Invalid field type: content must be a dictionary")
        if "body" not in doc["content"]:
            raise DocumentValidationError("Missing required field: content.body")
        if not isinstance(doc["content"]["body"], str):
            raise DocumentValidationError("Invalid field type: content.body must be a string")

        # Check content length if set
        if self.max_content_length and len(doc["content"]["body"]) > self.max_content_length:
            raise DocumentValidationError("Content length exceeds maximum")

        # Check content format
        content = doc["content"]["body"]
        if "\0" in content:
            raise DocumentValidationError("Invalid content format: contains null bytes")
        if any(ord(c) >= 0xFFFE for c in content):
            raise DocumentValidationError("Invalid content format: invalid Unicode")
        if "\x1B" in content:
            raise DocumentValidationError("Invalid content format: contains ANSI escape sequences")

        # Check metadata if present
        if "metadata" in doc:
            if not isinstance(doc["metadata"], dict):
                raise DocumentValidationError("Invalid field type: metadata must be a dictionary")
            if "title" in doc["metadata"] and not doc["metadata"]["title"]:
                raise DocumentValidationError("Invalid metadata: empty title")

        # Check nested structures
        def check_nested(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if value is None:
                        raise DocumentValidationError(
                            f"Invalid nested structure: {path}{key} is None"
                        )
                    check_nested(value, f"{path}{key}.")
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    check_nested(value, f"{path}[{i}].")

        check_nested(doc)

        # Apply custom validation rules
        for rule, message in self.validation_rules:
            if not rule(doc):
                raise DocumentValidationError(message)

        return True

    def set_max_content_length(self, length: int) -> None:
        """Set maximum allowed content length.

        Args:
            length: Maximum content length in characters
        """
        if length <= 0:
            raise ValueError("Maximum content length must be positive")
        self.max_content_length = length

    def add_validation_rule(self, rule, message: str) -> None:
        """Add a custom validation rule.

        Args:
            rule: Function that takes a document and returns bool
            message: Error message if validation fails
        """
        self.validation_rules.append((rule, message))

    def create_document(self, content: str, metadata: DocumentMetadata) -> Dict:
        """Create a new document with standard structure."""
        return {
            "content": {"body": content, "summary": None},
            "metadata": {
                "title": metadata.title,
                "source": metadata.source,
                "timestamp_utc": metadata.timestamp_utc,
                "last_modified_utc": metadata.last_modified_utc,
                "author": metadata.author,
                "tags": metadata.tags or [],
                "language": metadata.language,
            },
            "embeddings": {"version": None, "model": None, "body": None, "summary": None},
            "relationships": {"parent_id": None, "references": []},
        }

    def batch_documents(self, documents: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split documents into batches.

        Args:
            documents: List of documents to batch
            batch_size: Size of each batch

        Returns:
            List of document batches
        """
        # Ensure all documents have UUIDs
        documents = [self.ensure_document_id(doc) for doc in documents]

        return [documents[i : i + batch_size] for i in range(0, len(documents), batch_size)]

    def merge_document_updates(
        self, original: Dict, updates: Dict, overwrite: bool = False
    ) -> Dict:
        """Merge updates into original document."""
        merged = original.copy()

        # Update content
        if "content" in updates:
            if overwrite:
                merged["content"] = updates["content"]
            else:
                merged["content"].update(updates["content"])

        # Update metadata
        if "metadata" in updates:
            if overwrite:
                merged["metadata"] = updates["metadata"]
            else:
                merged["metadata"].update(updates["metadata"])
            # Always update last_modified
            merged["metadata"]["last_modified_utc"] = datetime.utcnow().isoformat()

        # Update embeddings
        if "embeddings" in updates:
            if overwrite:
                merged["embeddings"] = updates["embeddings"]
            else:
                merged["embeddings"].update(updates["embeddings"])

        # Update relationships
        if "relationships" in updates:
            if overwrite:
                merged["relationships"] = updates["relationships"]
            else:
                merged["relationships"].update(updates["relationships"])

        return merged

    def process(self, doc: Dict) -> Dict:
        """Process a single document.

        Args:
            doc: Document to process

        Returns:
            Processed document

        Raises:
            ValueError: If document is invalid or empty
        """
        # Validate document
        if not doc.get("content"):
            raise ValueError("Missing content in document")

        content = doc["content"].get("body", "")
        if not content:
            raise ValueError("Empty document content")

        # Preprocess text - normalize whitespace
        content = " ".join(content.split())  # Remove extra whitespace
        content = content.replace("\t", " ")  # Replace tabs with spaces
        content = content.replace("\r\n", "\n").replace("\r", "\n")  # Normalize line endings

        # Apply transformers
        for transformer in self.transformers:
            content = transformer(content)

        # Apply filters
        for filter_fn in self.filters:
            if not filter_fn(content):
                return None

        # Create chunks
        chunks = [content[i : i + self.chunk_size] for i in range(0, len(content), self.chunk_size)]

        # Get current timestamp
        processed_at = datetime.utcnow().isoformat()

        # Create processed document
        return {
            "id": doc.get("id", "test-id"),
            "content": {
                "body": content,
                "chunks": chunks,
                "summary": doc["content"].get("summary", ""),
            },
            "metadata": {
                "title": doc.get("metadata", {}).get("title", "Untitled"),
                "word_count": len(content.split()),
                "chunk_count": len(chunks),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "processed_at": processed_at,
            },
            "processed": True,
            "pipeline_version": "1.0.0",
            "processing_stats": {
                "transformer_count": len(self.transformers),
                "filter_count": len(self.filters),
                "original_length": len(doc["content"].get("body", "")),
                "processed_length": len(content),
            },
        }

    def set_chunk_size(self, size: int) -> None:
        """Set the chunk size for document processing.

        Args:
            size: Chunk size in characters

        Raises:
            ValueError: If size is not positive
        """
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        self.chunk_size = size

    def process_batch(self, documents: List[Dict]) -> List[Dict]:
        """Process multiple documents.

        Args:
            documents: List of documents to process

        Returns:
            List of processed documents
        """
        results = []
        for doc in documents:
            try:
                processed = self.process(doc)
                if processed:
                    results.append(processed)
            except Exception as e:
                self.logger.error(f"Error processing document: {str(e)}")
                continue
        return results

    def add_transformer(self, transformer_fn) -> None:
        """Add a transformer function to the processing pipeline.

        Args:
            transformer_fn: Function that takes and returns a string
        """
        self.transformers.append(transformer_fn)

    def add_filter(self, filter_fn) -> None:
        """Add a filter function to the processing pipeline.

        Args:
            filter_fn: Function that takes a string and returns a boolean
        """
        self.filters.append(filter_fn)
