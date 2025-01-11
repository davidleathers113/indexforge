"""Weaviate settings configuration."""

from typing import Optional

from pydantic import Field, field_validator

from src.api.config.settings import BaseAppSettings


class WeaviateSettings(BaseAppSettings):
    """Weaviate connection and operational settings."""

    # Connection Settings
    WEAVIATE_URL: str = Field(default="http://localhost:8080", description="Weaviate server URL")
    WEAVIATE_API_KEY: Optional[str] = Field(
        default=None, description="API key for Weaviate authentication"
    )
    WEAVIATE_PORT: Optional[int] = Field(default=8080, description="Weaviate server port")
    WEAVIATE_GRPC_PORT: int = Field(default=50051, description="Weaviate gRPC port")

    # Operation Settings
    WEAVIATE_BATCH_SIZE: int = Field(
        default=100, ge=1, le=1000, description="Number of objects per batch operation"
    )
    WEAVIATE_TIMEOUT: int = Field(
        default=30, ge=5, le=300, description="Operation timeout in seconds"
    )
    WEAVIATE_CONNECTION_TIMEOUT: int = Field(
        default=10, ge=1, le=60, description="Connection timeout in seconds"
    )
    WEAVIATE_TIMEOUT_RETRIES: int = Field(
        default=3, ge=0, le=10, description="Number of retry attempts"
    )
    WEAVIATE_QUERY_DEFAULTS_LIMIT: int = Field(
        default=25, ge=1, le=100, description="Default limit for query results"
    )
    WEAVIATE_ENABLE_GRPC: bool = Field(default=True, description="Enable gRPC support")

    @field_validator("WEAVIATE_URL")
    @classmethod
    def validate_weaviate_url(cls, v: str) -> str:
        """Validate Weaviate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("WEAVIATE_URL must start with http:// or https://")
        return v

    @field_validator("WEAVIATE_BATCH_SIZE")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size is within reasonable limits."""
        if not 1 <= v <= 1000:
            raise ValueError("WEAVIATE_BATCH_SIZE must be between 1 and 1000")
        return v
