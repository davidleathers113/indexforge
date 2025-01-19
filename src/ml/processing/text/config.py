"""Text processing configuration.

This module defines configuration settings for text processing operations,
including cleaning, chunking, and analysis parameters.
"""

from pydantic import BaseModel, Field, field_validator


class TextProcessingConfig(BaseModel):
    """Configuration for text processing operations."""

    # Cleaning settings
    strip_whitespace: bool = Field(default=True, description="Whether to strip excess whitespace")
    normalize_unicode: bool = Field(
        default=True, description="Whether to normalize Unicode characters"
    )

    # Chunking settings
    max_chunk_size: int = Field(default=1000, description="Maximum characters per chunk", gt=0)
    chunk_overlap: int = Field(
        default=100, description="Number of characters to overlap between chunks", ge=0
    )

    # Analysis settings
    detect_language: bool = Field(default=True, description="Whether to detect text language")
    min_confidence: float = Field(
        default=0.8, description="Minimum confidence for language detection", ge=0.0, le=1.0
    )
    encoding: str = Field(default="utf-8", description="Expected text encoding")

    @field_validator("chunk_overlap")
    def validate_overlap(cls, v: int, info) -> int:
        """Validate that chunk overlap is less than chunk size.

        Args:
            v: The overlap value to validate
            info: ValidationInfo instance containing the model data

        Returns:
            The validated overlap value

        Raises:
            ValueError: If overlap is greater than chunk size
        """
        if v >= info.data.get("max_chunk_size", 1000):
            raise ValueError("Chunk overlap must be less than chunk size")
        return v

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
        extra = "forbid"
