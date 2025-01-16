"""Direct documentation indexing connector for file processing.

This module provides the main connector for processing document files directly
from the filesystem. It manages multiple file type processors and handles the
routing of files to appropriate processors based on their type.

The connector supports automatic processor selection and provides a unified
interface for processing different types of document files.
"""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class DocumentConnector:
    """Manages document file processing with type-specific processors.

    This class serves as the main entry point for processing document files.
    It maintains a collection of specialized processors for different file
    types and automatically routes files to the appropriate processor.

    Attributes:
        processors (Dict): Dictionary mapping file types to their processors.

    Example:
        ```python
        connector = DocumentConnector()

        # Process an Excel file
        excel_result = connector.process_file("data.xlsx")

        # Process a Word document
        word_result = connector.process_file("document.docx")
        ```
    """

    def __init__(self):
        """Initialize the document connector.

        Sets up the connector with an empty processor dictionary.
        Processors should be added using the processors property.
        """
        self._processors = {}

    @property
    def processors(self) -> dict:
        """Get the dictionary of file type processors."""
        return self._processors

    @processors.setter
    def processors(self, value: dict):
        """Set the dictionary of file type processors."""
        self._processors = value

    def process_file(self, file_path: str | Path) -> dict:
        """Process a document file using the appropriate processor.

        Attempts to process the given file by:
        1. Converting the file path to a Path object
        2. Verifying file existence
        3. Finding a suitable processor based on file type
        4. Processing the file with the selected processor

        Args:
            file_path: Path to the document file to process. Can be
                either a string path or a Path object.

        Returns:
            Dict: Processing result containing:
                - status: "success" or "error"
                - message: Error message if status is "error"
                - content: Extracted content if status is "success"
                - metadata: File metadata if status is "success"

        Example:
            ```python
            connector = DocumentConnector()
            result = connector.process_file("data.xlsx")

            if result["status"] == "success":
                content = result["content"]
                metadata = result["metadata"]
            else:
                error_msg = result["message"]
            ```

        Note:
            If no suitable processor is found for the file type, or if
            processing fails, returns a dictionary with error status
            and message.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"status": "error", "message": "File not found"}

            # Try each processor
            for processor in self.processors.values():
                if processor.can_process(file_path):
                    return processor.process(file_path)

            return {"status": "error", "message": f"No suitable processor found for {file_path}"}
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e!s}")
            return {"status": "error", "message": str(e), "file": str(file_path)}
