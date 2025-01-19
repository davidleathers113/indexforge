"""Document processing error types.

This module defines custom exceptions for document processing operations.
"""

from typing import Optional


class DocumentError(Exception):
    """Base class for document processing errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message)
        self.details = details or {}


class DocumentProcessingError(DocumentError):
    """Error during document processing operations."""

    pass


class DocumentValidationError(DocumentError):
    """Error during document validation."""

    pass


class UnsupportedDocumentError(DocumentError):
    """Error when document type is not supported."""

    pass


class DocumentConfigError(DocumentError):
    """Error in document processing configuration."""

    pass


class ResourceError(DocumentError):
    """Error managing processor resources."""

    pass
