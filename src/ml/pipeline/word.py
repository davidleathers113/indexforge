"""Word document processor for ML pipeline.

This module provides specialized processing for Word documents (.docx, .doc).
It handles extraction of text content and metadata while preserving document
structure information like paragraphs, headers, and formatting.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set

import docx
from pydantic import Field

from .base import BaseProcessor
from .config.settings import PipelineConfig, ProcessingConfig


class WordProcessingConfig(ProcessingConfig):
    """Configuration for Word document processing.

    Extends the base ProcessingConfig with Word-specific settings.
    """

    extract_headers: bool = Field(
        default=True, description="Whether to extract headers and include in content"
    )
    preserve_formatting: bool = Field(
        default=False, description="Whether to preserve text formatting information"
    )
    max_paragraph_length: int = Field(
        default=5000, description="Maximum characters per paragraph", gt=0
    )


class WordProcessor(BaseProcessor):
    """Processor for Word documents.

    Handles the extraction and processing of content from Word files,
    maintaining document structure and handling large files efficiently.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        processing_config: Optional[WordProcessingConfig] = None,
    ) -> None:
        """Initialize the Word processor.

        Args:
            config: Optional pipeline configuration
            processing_config: Optional Word-specific processing configuration
        """
        super().__init__(
            config=config, processing_config=processing_config or WordProcessingConfig()
        )
        self._word_config: WordProcessingConfig = self.processing_config  # type: ignore
        self._processed_files: Set[Path] = set()

    def _validate_config(self) -> None:
        """Validate the processor configuration.

        Extends the base validation to ensure Word-specific config is valid.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(self.processing_config, WordProcessingConfig):
            raise ValueError("processing_config must be an instance of WordProcessingConfig")

    def initialize(self) -> None:
        """Initialize the processor.

        Performs Word-specific initialization tasks.
        """
        super().initialize()
        self._processed_files.clear()

    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process a Word file.

        Args:
            file_path: Path to the Word file to process

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

        if file_path.suffix.lower() not in {".docx", ".doc"}:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        try:
            # Read Word document
            doc = docx.Document(file_path)

            processed_paragraphs = []
            total_content = []

            # Process paragraphs
            for paragraph in doc.paragraphs:
                if len(paragraph.text) > self._word_config.max_paragraph_length:
                    raise ValueError(
                        f"Paragraph exceeds maximum length of "
                        f"{self._word_config.max_paragraph_length} characters"
                    )

                # Process paragraph content
                paragraph_content = self._process_paragraph(paragraph)
                if paragraph_content:
                    processed_paragraphs.append(paragraph_content)
                    total_content.append(paragraph_content["text"])

            # Update processed files tracking
            self._processed_files.add(file_path)

            return {
                "content": " ".join(total_content),
                "metadata": {
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower(),
                    "total_paragraphs": len(processed_paragraphs),
                    "has_headers": self._word_config.extract_headers,
                },
                "structure": processed_paragraphs,
            }

        except Exception as e:
            raise ValueError(f"Error processing Word file: {str(e)}") from e

    def _process_paragraph(self, paragraph: Any) -> Dict[str, Any]:
        """Process a single paragraph from the Word file.

        Args:
            paragraph: docx Paragraph object containing the paragraph data

        Returns:
            Dict containing paragraph-specific information and content
        """
        # Skip empty paragraphs
        if not paragraph.text.strip():
            return {}

        result = {
            "text": paragraph.text,
            "style": paragraph.style.name if self._word_config.preserve_formatting else None,
        }

        if self._word_config.extract_headers and paragraph.style.name.startswith("Heading"):
            result["is_header"] = True
            result["header_level"] = int(paragraph.style.name.replace("Heading", ""))

        return result

    def cleanup(self) -> None:
        """Clean up processor resources.

        Performs Word-specific cleanup tasks.
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
