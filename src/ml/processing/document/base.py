"""Base document processor implementation.

This module provides the base processor class with common functionality for
document processing operations, including configuration management, validation,
and resource handling.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.interfaces.processing import ChunkProcessor
from src.ml.processing.document.config import DocumentProcessingConfig
from src.ml.processing.document.errors import (
    DocumentProcessingError,
    DocumentValidationError,
    UnsupportedDocumentError,
)


class ProcessingResult:
    """Result of document processing operation.

    Attributes:
        status: Processing status ("success" or "error")
        content: Extracted content and metadata
        errors: List of error messages if status is "error"
    """

    def __init__(
        self,
        status: str = "success",
        content: Optional[Dict[str, Any]] = None,
        errors: Optional[list[str]] = None,
    ):
        self.status = status
        self.content = content or {}
        self.errors = errors or []


class BaseDocumentProcessor(ChunkProcessor, ABC):
    """Base class for document processors.

    Provides common functionality for document processing, including:
    - Configuration management
    - File validation
    - Resource cleanup
    - Error handling
    - Metadata tracking

    Args:
        config: Document processing configuration
        logger: Optional logger instance
    """

    def __init__(
        self,
        config: Optional[DocumentProcessingConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or DocumentProcessingConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._initialized = False
        self._metadata: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Initialize processor resources.

        Should be called before processing any documents.

        Raises:
            DocumentProcessingError: If initialization fails
        """
        try:
            self._initialize_resources()
            self._initialized = True
            self.logger.info("Processor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize processor: {e!s}")
            raise DocumentProcessingError(f"Initialization failed: {e!s}") from e

    def cleanup(self) -> None:
        """Clean up processor resources.

        Should be called when processor is no longer needed.
        """
        try:
            self._cleanup_resources()
            self._initialized = False
            self.logger.info("Processor cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e!s}")
            raise DocumentProcessingError(f"Cleanup failed: {e!s}") from e

    def can_process(self, file_path: Path) -> bool:
        """Check if processor can handle the given file.

        Args:
            file_path: Path to document file

        Returns:
            bool: True if processor can handle the file
        """
        return file_path.suffix.lower() in self.config.supported_extensions

    def process(self, file_path: Path) -> ProcessingResult:
        """Process a document file.

        Args:
            file_path: Path to document file

        Returns:
            ProcessingResult: Processing result with content and status

        Raises:
            DocumentValidationError: If document validation fails
            UnsupportedDocumentError: If document type is not supported
            DocumentProcessingError: If processing fails
        """
        if not self._initialized:
            raise DocumentProcessingError("Processor not initialized")

        try:
            # Validate file
            self._validate_file(file_path)

            # Process document
            content = self._process_document(file_path)

            # Track metadata
            self._update_metadata(file_path, content)

            return ProcessingResult(status="success", content=content)

        except DocumentValidationError as e:
            self.logger.error(f"Validation error for {file_path}: {e!s}")
            return ProcessingResult(status="error", errors=[str(e)])
        except UnsupportedDocumentError as e:
            self.logger.error(f"Unsupported document {file_path}: {e!s}")
            return ProcessingResult(status="error", errors=[str(e)])
        except Exception as e:
            self.logger.error(f"Processing error for {file_path}: {e!s}")
            return ProcessingResult(status="error", errors=[str(e)])

    def get_metadata(self) -> Dict[str, Any]:
        """Get processor metadata.

        Returns:
            Dict[str, Any]: Processor metadata
        """
        return self._metadata.copy()

    def _validate_file(self, file_path: Path) -> None:
        """Validate document file.

        Args:
            file_path: Path to document file

        Raises:
            DocumentValidationError: If validation fails
            UnsupportedDocumentError: If file type is not supported
        """
        if not file_path.exists():
            raise DocumentValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise DocumentValidationError(f"Not a file: {file_path}")

        if not self.can_process(file_path):
            raise UnsupportedDocumentError(f"Unsupported file type: {file_path.suffix}")

        if self.config.max_file_size > 0:
            size = file_path.stat().st_size
            if size > self.config.max_file_size:
                raise DocumentValidationError(
                    f"File too large: {size} bytes (max {self.config.max_file_size})"
                )

    def _update_metadata(self, file_path: Path, content: Dict[str, Any]) -> None:
        """Update processor metadata.

        Args:
            file_path: Path to processed file
            content: Extracted content
        """
        self._metadata.setdefault("processed_files", 0)
        self._metadata["processed_files"] += 1
        self._metadata["last_file"] = str(file_path)
        self._metadata["last_file_size"] = file_path.stat().st_size
        if "metadata" in content:
            self._metadata.setdefault("document_metadata", []).append(content["metadata"])

    @abstractmethod
    def _initialize_resources(self) -> None:
        """Initialize processor-specific resources.

        Raises:
            DocumentProcessingError: If initialization fails
        """
        pass

    @abstractmethod
    def _cleanup_resources(self) -> None:
        """Clean up processor-specific resources.

        Raises:
            DocumentProcessingError: If cleanup fails
        """
        pass

    @abstractmethod
    def _process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process a document file.

        Args:
            file_path: Path to document file

        Returns:
            Dict[str, Any]: Extracted content and metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        pass
