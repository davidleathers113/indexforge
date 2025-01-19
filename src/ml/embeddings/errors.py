"""Embedding-related error types.

This module defines the error hierarchy for embedding operations,
providing structured error handling with error codes and context.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Base class for embedding-related errors."""

    def __init__(self, message: str, code: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the error.

        Args:
            message: Error description
            code: Error code for categorization
            details: Optional error context details
        """
        self.code = code
        self.details = details or {}
        super().__init__(f"{code}: {message}")
        logger.exception(
            "Embedding error occurred: %s", message, extra={"code": code, "details": self.details}
        )


class ValidationError(EmbeddingError):
    """Raised when chunk validation fails."""

    def __init__(
        self, message: str, validation_errors: List[str], chunk_id: Optional[str] = None
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            validation_errors: List of specific validation failures
            chunk_id: Optional ID of the failed chunk
        """
        details = {"validation_errors": validation_errors, "chunk_id": chunk_id}
        super().__init__(message, "VALIDATION_ERROR", details)
        self.validation_errors = validation_errors


class GeneratorError(EmbeddingError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, model_name: str, batch_size: Optional[int] = None) -> None:
        """Initialize generator error.

        Args:
            message: Error description
            model_name: Name of the model that failed
            batch_size: Optional batch size that caused the error
        """
        details = {"model_name": model_name, "batch_size": batch_size}
        super().__init__(message, "GENERATOR_ERROR", details)
