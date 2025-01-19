"""Base processor interface for document file processing.

This module defines the abstract base class for document processors that handle
different file types. It provides a common interface for file processing operations
including file type validation, content extraction, and metadata collection.

The base processor defines a consistent interface that all document processors must
implement, ensuring uniform handling of different file types while allowing for
type-specific optimizations and features.

Example:
    ```python
    class PDFProcessor(BaseProcessor):
        def can_process(self, file_path: Path) -> bool:
            return file_path.suffix.lower() == ".pdf"

        def process(self, file_path: Path) -> ProcessingResult:
            try:
                content = self._extract_pdf_content(file_path)
                return ProcessingResult.success(content)
            except Exception as e:
                return ProcessingResult.error(str(e))
    ```
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, TypedDict


logger = logging.getLogger(__name__)


class FileMetadata(TypedDict):
    """Type definition for file metadata.

    Attributes:
        file_name: Name of the file
        file_path: Full path to the file
        file_size: Size of file in bytes
        modified_time: Last modification timestamp
        created_time: Creation timestamp
    """

    file_name: str
    file_path: str
    file_size: int
    modified_time: float
    created_time: float


@dataclass
class ProcessingResult:
    """Result of document processing operation.

    This class provides a standardized way to return processing results,
    including success/failure status, content, and error information.

    Attributes:
        status: Processing status ("success" or "error")
        content: Extracted content and metadata
        error: Error message if processing failed

    Example:
        ```python
        try:
            content = process_document(file_path)
            return ProcessingResult.success(content)
        except Exception as e:
            return ProcessingResult.error(str(e))
        ```
    """

    status: str
    content: dict[str, Any]
    error: str | None = None

    @classmethod
    def success(cls, content: dict[str, Any]) -> "ProcessingResult":
        """Create a successful processing result.

        Args:
            content: Extracted content and metadata

        Returns:
            ProcessingResult: Successful result with content
        """
        return cls(status="success", content=content)

    @classmethod
    def create_error(
        cls, error_msg: str, partial_content: dict[str, Any] | None = None
    ) -> "ProcessingResult":
        """Create an error processing result.

        Args:
            error_msg: Description of the error
            partial_content: Any content that was extracted before the error

        Returns:
            ProcessingResult: Error result with message and optional partial content
        """
        return cls(status="error", content=partial_content or {}, error=error_msg)


class BaseProcessor(ABC):
    """Abstract base class for document file processors.

    This class defines the interface that all document processors must implement.
    It provides common functionality for file processing, including configuration
    management and metadata extraction. Specific file type processors should
    inherit from this class and implement the abstract methods.

    Attributes:
        config: Configuration dictionary for the processor

    Example:
        ```python
        processor = ConcreteProcessor({
            "encoding": "utf-8",
            "chunk_size": 1024
        })
        ```
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the document processor.

        Sets up the processor with optional configuration parameters that can
        customize the processing behavior.

        Args:
            config: Optional configuration dictionary containing processor settings.
                   If None, an empty dictionary is used.
        """
        self.config = config or {}

    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file type.

        Determines whether this processor is capable of processing the file
        at the given path, typically by checking file extension or content.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if this processor can handle the file, False otherwise

        Example:
            ```python
            if processor.can_process(Path("document.pdf")):
                result = processor.process(Path("document.pdf"))
            ```
        """
        pass

    @abstractmethod
    def process(self, file_path: Path) -> ProcessingResult:
        """Process a file and extract its content and metadata.

        Processes the file at the given path, extracting text content,
        metadata, and any other relevant information. Handles any necessary
        file operations and content transformations.

        Args:
            file_path: Path to the file to process

        Returns:
            ProcessingResult: Processing result containing status, content, and any error

        Raises:
            IOError: If file cannot be read or processed
            ValueError: If file content is invalid or malformed

        Example:
            ```python
            result = processor.process(Path("document.txt"))
            if result.status == "success":
                print(f"Extracted content: {result.content}")
            else:
                print(f"Processing failed: {result.error}")
            ```
        """
        pass

    def _get_file_metadata(self, file_path: Path) -> FileMetadata:
        """Extract basic file metadata.

        Collects standard file system metadata for the given file, including
        file name, path, size, and timestamps.

        Args:
            file_path: Path to the file to get metadata for

        Returns:
            FileMetadata: Dictionary containing file metadata

        Example:
            ```python
            metadata = processor._get_file_metadata(Path("document.pdf"))
            print(f"File size: {metadata['file_size']} bytes")
            ```
        """
        try:
            stats = file_path.stat()
            return FileMetadata(
                file_name=file_path.name,
                file_path=str(file_path),
                file_size=stats.st_size,
                modified_time=stats.st_mtime,
                created_time=stats.st_ctime,
            )
        except OSError as e:
            logger.error(f"Error getting metadata for {file_path}: {e!s}")
            raise OSError(f"Failed to get file metadata: {e!s}") from e
