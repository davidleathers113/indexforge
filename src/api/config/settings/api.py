"""API settings configuration."""

from typing import Any

from pydantic import Field

from .base import BaseAppSettings


class APISettings(BaseAppSettings):
    """API settings."""

    title: str = Field(default="IndexForge API", description="API title")
    description: str = Field(
        default="Universal file indexing and processing system",
        description="API description",
    )
    version: str = Field(default="0.1.0", description="API version")
    docs_url: str = Field(default="/docs", description="API documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc documentation URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI schema URL")
    root_path: str = Field(default="", description="API root path")
    root_path_in_servers: bool = Field(
        default=True, description="Include root path in OpenAPI servers"
    )

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Override dict to include nested settings."""
        base_dict = super().dict(*args, **kwargs)
        return {
            **base_dict,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
            "openapi_url": self.openapi_url,
            "root_path": self.root_path,
            "root_path_in_servers": self.root_path_in_servers,
        }
