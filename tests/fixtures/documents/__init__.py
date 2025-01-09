"""Document fixtures for testing.

This module provides document-related functionality:
- Document state management
- Document processing
- Sample documents and test data
"""

from .fixtures import (
    document_with_relationships,
    large_document,
    sample_data,
    sample_document,
    sample_documents,
)
from .processor import mock_doc_processor
from .state import DocumentState, doc_state

__all__ = [
    "DocumentState",
    "doc_state",
    "mock_doc_processor",
    "sample_data",
    "sample_document",
    "sample_documents",
    "document_with_relationships",
    "large_document",
]
