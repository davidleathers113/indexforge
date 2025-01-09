"""Base processor interface for document file processing.

This module defines the abstract base class for document processors that handle
different file types. It provides a common interface for file processing operations
including file type validation, content extraction, and metadata collection.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseProcessor(ABC):
    """Abstract base class for document file processors.

    This class defines the interface that all document processors must implement.
    It provides common functionality for file processing, including configuration
    management and metadata extraction. Specific file type processors should
    inherit from this class and implement the abstract methods.

    Attributes:
        config (Dict[str, Any]): Configuration dictionary for the processor.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the document processor.

        Sets up the processor with optional configuration parameters that can
        customize the processing behavior.

        Args:
            config: Optional configuration dictionary containing processor settings.
                   If None, an empty dictionary is used.

        Example:
            ```python
            processor = ConcreteProcessor({
                "encoding": "utf-8",
                "chunk_size": 1024
            })
            ```
        """
        self.config = config or {}

    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file type.

        Determines whether this processor is capable of processing the file
        at the given path, typically by checking file extension or content.

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if this processor can handle the file, False otherwise.

        Example:
            ```python
            if processor.can_process(Path("document.pdf")):
                result = processor.process(Path("document.pdf"))
            ```
        """
        pass

    @abstractmethod
    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process a file and extract its content and metadata.

        Processes the file at the given path, extracting text content,
        metadata, and any other relevant information. Handles any necessary
        file operations and content transformations.

        Args:
            file_path: Path to the file to process.

        Returns:
            Dict[str, Any]: Dictionary containing:
                - content (Dict): Extracted text and metadata
                - status (str): Processing status ("success" or "error")
                - error (Optional[str]): Error message if processing failed

        Raises:
            IOError: If file cannot be read or processed.
            ValueError: If file content is invalid or malformed.

        Example:
            ```python
            result = processor.process(Path("document.txt"))
            if result["status"] == "success":
                print(f"Extracted content: {result['content']}")
            else:
                print(f"Processing failed: {result['error']}")
            ```
        """
        pass

    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file metadata.

        Collects standard file system metadata for the given file, including
        file name, path, size, and timestamps.

        Args:
            file_path: Path to the file to get metadata for.

        Returns:
            Dict[str, Any]: Dictionary containing:
                - file_name (str): Name of the file
                - file_path (str): Full path to the file
                - file_size (int): Size of file in bytes
                - modified_time (float): Last modification timestamp
                - created_time (float): Creation timestamp

        Example:
            ```python
            metadata = processor._get_file_metadata(Path("document.pdf"))
            print(f"File size: {metadata['file_size']} bytes")
            ```
        """
        stats = file_path.stat()
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": stats.st_size,
            "modified_time": stats.st_mtime,
            "created_time": stats.st_ctime,
        }
