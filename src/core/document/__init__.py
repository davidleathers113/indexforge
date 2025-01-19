"""Document processing and operations module.

This module provides functionality for document operations, including:
- Document creation and modification
- Document relationship management
- Document state tracking
- Document validation and verification
"""

from .models import Document, DocumentMetadata, DocumentRelationship
from .operations import DocumentNotFoundError, DocumentOperationError, DocumentOperationsService


__all__ = [
    # Document service
    "DocumentOperationsService",
    # Document models
    "Document",
    "DocumentMetadata",
    "DocumentRelationship",
    # Exceptions
    "DocumentOperationError",
    "DocumentNotFoundError",
]
