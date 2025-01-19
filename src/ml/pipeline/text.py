"""Text document processor for ML pipeline.

This module provides specialized processing for text documents (.txt, .md).
It handles extraction of text content and metadata while preserving document
structure information like paragraphs and sections.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set

from pydantic import Field

from .base import BaseProcessor
from .config.settings import PipelineConfig, ProcessingConfig


class TextProcessingConfig(ProcessingConfig):
    """Configuration for text document processing.

    Extends the base ProcessingConfig with text-specific settings.
    """

    detect_paragraphs: bool = Field(
        default=True, description="Whether to detect and preserve paragraph breaks"
    )
    strip_whitespace: bool = Field(default=True, description="Whether to strip excess whitespace")
    max_line_length: int = Field(default=1000, description="Maximum characters per line", gt=0)


class TextProcessor(BaseProcessor):
    """Processor for text documents.

    Handles the extraction and processing of content from text files,
    maintaining document structure and handling large files efficiently.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        processing_config: Optional[TextProcessingConfig] = None,
    ) -> None:
        """Initialize the text processor.

        Args:
            config: Optional pipeline configuration
            processing_config: Optional text-specific processing configuration
        """
        super().__init__(
            config=config, processing_config=processing_config or TextProcessingConfig()
        )
        self._text_config: TextProcessingConfig = self.processing_config  # type: ignore
        self._processed_files: Set[Path] = set()

    def _validate_config(self) -> None:
        """Validate the processor configuration.

        Extends the base validation to ensure text-specific config is valid.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(self.processing_config, TextProcessingConfig):
            raise ValueError("processing_config must be an instance of TextProcessingConfig")

    def initialize(self) -> None:
        """Initialize the processor.

        Performs text-specific initialization tasks.
        """
        super().initialize()
        self._processed_files.clear()

    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process a text file.

        Args:
            file_path: Path to the text file to process

        Returns:
            Dict containing:
                - content: Extracted text content
                - metadata: File and processing metadata
                - structure: Document structure information

        Raises:
            RuntimeError: If the processor is not initialized
            ValueError: If the file is invalid or cannot be processed
            IOError: If there are issues reading the file
        """
        super().process(file_path)

        if not isinstance(file_path, Path):
            raise ValueError("file_path must be a Path object")

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in {".txt", ".md"}:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        try:
            # Read text file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Process content
            processed_lines = []
            total_content = []

            # Split into paragraphs if configured
            paragraphs = content.split("\n\n") if self._text_config.detect_paragraphs else [content]

            for paragraph in paragraphs:
                # Process lines in paragraph
                lines = paragraph.splitlines()
                for line in lines:
                    if len(line) > self._text_config.max_line_length:
                        raise ValueError(
                            f"Line exceeds maximum length of "
                            f"{self._text_config.max_line_length} characters"
                        )

                    # Process line content
                    line_content = self._process_line(line)
                    if line_content:
                        processed_lines.append(line_content)
                        total_content.append(line_content["text"])

            # Update processed files tracking
            self._processed_files.add(file_path)

            return {
                "content": " ".join(total_content),
                "metadata": {
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower(),
                    "total_lines": len(processed_lines),
                    "detect_paragraphs": self._text_config.detect_paragraphs,
                },
                "structure": processed_lines,
            }

        except Exception as e:
            raise ValueError(f"Error processing text file: {str(e)}") from e

    def _process_line(self, line: str) -> Dict[str, Any]:
        """Process a single line from the text file.

        Args:
            line: String containing the line content

        Returns:
            Dict containing line-specific information and content
        """
        # Skip empty lines
        if not line.strip():
            return {}

        # Strip whitespace if configured
        text = line.strip() if self._text_config.strip_whitespace else line

        return {
            "text": text,
            "length": len(text),
            "is_empty": False,
        }

    def cleanup(self) -> None:
        """Clean up processor resources.

        Performs text-specific cleanup tasks.
        """
        self._processed_files.clear()
        super().cleanup()

    @property
    def processed_files(self) -> Set[Path]:
        """Get the set of processed file paths.

        Returns:
            Set of Path objects for processed files
        """
        return self._processed_files.copy()
