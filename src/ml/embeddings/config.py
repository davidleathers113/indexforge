"""Configuration management for embedding operations.

This module provides structured configuration management using Pydantic,
ensuring type safety and validation of configuration values.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ValidatorConfig(BaseModel):
    """Configuration for chunk validation."""

    min_words: int = Field(
        default=3, description="Minimum number of words required in a chunk", ge=1
    )
    min_size: int = Field(default=1024, description="Minimum chunk size in bytes", ge=1)  # 1KB
    max_size: int = Field(
        default=1024 * 1024, description="Maximum chunk size in bytes", ge=1024  # 1MB
    )

    @field_validator("max_size")
    @classmethod
    def validate_size_range(cls, v: int, info) -> int:
        """Validate that max_size is greater than min_size.

        Args:
            v: The value to validate
            info: ValidationInfo instance containing the values

        Returns:
            The validated value

        Raises:
            ValueError: If max_size is not greater than min_size
        """
        values = info.data
        if "min_size" in values and v <= values["min_size"]:
            raise ValueError("max_size must be greater than min_size")
        return v


class GeneratorConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str = Field(
        ..., description="Name of the transformer model to use"  # Required field
    )
    batch_size: int = Field(default=32, description="Batch size for processing", ge=1)
    device: Optional[str] = Field(
        default=None, description="Device to run the model on (cpu, cuda, etc.)"
    )

    class Config:
        """Pydantic model configuration."""

        env_prefix = "EMBEDDING_"  # Environment variables prefix
