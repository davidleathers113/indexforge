"""Pipeline configuration settings.

This module defines the configuration settings for the ML pipeline using Pydantic models.
It provides type-safe configuration with validation and environment variable support.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ProcessingConfig(BaseModel):
    """Configuration for document processing settings."""

    batch_size: int = Field(
        default=100, description="Number of documents to process in each batch", gt=0, le=1000
    )
    min_document_length: int = Field(
        default=50, description="Minimum length of documents to process", gt=0
    )
    max_document_length: int = Field(
        default=8192, description="Maximum length of documents to process", gt=0
    )

    @field_validator("max_document_length")
    @classmethod
    def validate_document_length(cls, v: int, info):
        """Validate that max_document_length is greater than min_document_length."""
        if "min_document_length" in info.data and v <= info.data["min_document_length"]:
            raise ValueError("max_document_length must be greater than min_document_length")
        return v


class CacheConfig(BaseModel):
    """Configuration for caching settings."""

    host: str = Field(default="localhost", description="Redis cache host address")
    port: int = Field(default=6379, description="Redis cache port number", gt=0, le=65535)
    ttl: int = Field(default=86400, description="Cache TTL in seconds", gt=0)
    prefix: str = Field(default="pipeline", description="Cache key prefix for pipeline operations")


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""

    max_retries: int = Field(default=3, description="Maximum number of retry attempts", ge=0)
    backoff_factor: float = Field(
        default=0.1, description="Exponential backoff factor for retries", ge=0
    )
    max_backoff: int = Field(default=60, description="Maximum backoff time in seconds", gt=0)


class PipelineConfig(BaseSettings):
    """Main configuration settings for the ML pipeline.

    This class uses Pydantic's BaseSettings to support loading from environment variables.
    Environment variables are prefixed with 'PIPELINE_' by default.
    """

    export_dir: Path = Field(default=Path("exports"), description="Directory for document exports")
    log_dir: Path = Field(default=Path("logs"), description="Directory for log files")
    index_url: str = Field(
        default="http://localhost:8080", description="URL of the vector index service"
    )
    class_name: str = Field(default="Document", description="Document class name in vector index")

    # Component configurations
    processing: ProcessingConfig = Field(
        default_factory=ProcessingConfig, description="Document processing settings"
    )
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache settings")
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry behavior settings")

    class Config:
        env_prefix = "PIPELINE_"
        case_sensitive = False

    @field_validator("export_dir", "log_dir")
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        """Ensure directories exist and are writable."""
        v.mkdir(parents=True, exist_ok=True)
        if not v.is_dir():
            raise ValueError(f"Path {v} is not a directory")
        return v
