"""
Schema validation components for document processing.

This package provides validation functionality for:
- Document field validation
- Relationship validation
- Embedding validation
- Schema compliance checks

Example:
    ```python
    from src.indexing.schema.validators import (
        validate_document_fields,
        validate_relationships,
        validate_embedding
    )
    ```
"""

from .document import validate_document_fields
from .embedding import validate_embedding, validate_embedding_batch
from .relationship import validate_relationships

__all__ = [
    "validate_document_fields",
    "validate_embedding",
    "validate_embedding_batch",
    "validate_relationships",
]
