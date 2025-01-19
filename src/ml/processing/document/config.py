"""Document processing configuration.

This module provides configuration settings for document processing operations,
including settings for different document types and processing options.
"""

from typing import List, Set

from pydantic import BaseModel, Field, field_validator


class ExcelProcessingConfig(BaseModel):
    """Configuration for Excel document processing.

    Attributes:
        max_rows: Maximum number of rows to process (0 for unlimited)
        max_cols: Maximum number of columns to process (0 for unlimited)
        sheet_names: Specific sheets to process (empty for all sheets)
        header_row: Row number containing headers (0-based)
        skip_empty: Whether to skip empty cells
        required_columns: List of required column names
    """

    max_rows: int = Field(default=0, ge=0)
    max_cols: int = Field(default=0, ge=0)
    sheet_names: Set[str] = Field(default_factory=set)
    header_row: int = Field(default=0, ge=0)
    skip_empty: bool = Field(default=True)
    required_columns: List[str] = Field(default_factory=list)


class WordProcessingConfig(BaseModel):
    """Configuration for Word document processing.

    Attributes:
        extract_headers: Whether to extract document headers
        extract_tables: Whether to extract tables
        extract_images: Whether to extract image metadata
        max_image_size: Maximum image size in bytes (0 for unlimited)
        preserve_formatting: Whether to preserve text formatting
    """

    extract_headers: bool = Field(default=True)
    extract_tables: bool = Field(default=True)
    extract_images: bool = Field(default=False)
    max_image_size: int = Field(default=0, ge=0)
    preserve_formatting: bool = Field(default=False)


class DocumentProcessingConfig(BaseModel):
    """Configuration for document processing.

    Attributes:
        excel_config: Configuration for Excel processing
        word_config: Configuration for Word processing
        max_file_size: Maximum file size in bytes (0 for unlimited)
        supported_extensions: Set of supported file extensions
        extract_metadata: Whether to extract document metadata
        validate_content: Whether to validate document content
        chunk_size: Size of chunks for processing (0 for no chunking)
    """

    excel_config: ExcelProcessingConfig = Field(default_factory=ExcelProcessingConfig)
    word_config: WordProcessingConfig = Field(default_factory=WordProcessingConfig)
    max_file_size: int = Field(default=0, ge=0)
    supported_extensions: Set[str] = Field(
        default_factory=lambda: {".xlsx", ".xls", ".csv", ".docx", ".doc"}
    )
    extract_metadata: bool = Field(default=True)
    validate_content: bool = Field(default=True)
    chunk_size: int = Field(default=0, ge=0)

    @classmethod
    @field_validator("supported_extensions")
    def validate_extensions(cls, v: Set[str]) -> Set[str]:
        """Validate file extensions.

        Args:
            v: Set of file extensions

        Returns:
            Set[str]: Validated extensions

        Raises:
            ValueError: If any extension is invalid
        """
        for ext in v:
            if not ext.startswith("."):
                raise ValueError(f"Extension must start with '.': {ext}")
            if not ext[1:].isalnum():
                raise ValueError(f"Invalid extension format: {ext}")
        return v
