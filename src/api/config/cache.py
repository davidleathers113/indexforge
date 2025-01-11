"""Cache settings configuration."""

from typing import Literal

from pydantic import Field, field_validator

from src.api.config.base import BaseAppSettings


class CacheSettings(BaseAppSettings):
    """Cache settings."""

    # Cache strategy configuration
    CACHE_STRATEGY: Literal["simple", "two_level", "query"] = Field(
        "simple", description="Cache strategy type"
    )
    CACHE_PROVIDER: Literal["memory", "redis", "null"] = Field(
        "memory", description="Cache provider type"
    )

    # Cache size and TTL
    CACHE_MAX_SIZE: int = Field(1000, ge=1, description="Maximum cache size")
    CACHE_TTL: int = Field(300, ge=1, description="Default cache TTL in seconds")

    # Redis configuration
    REDIS_HOST: str = Field("localhost", description="Redis host")
    REDIS_PORT: int = Field(6379, ge=1, le=65535, description="Redis port")

    @field_validator("CACHE_MAX_SIZE")
    @classmethod
    def validate_cache_max_size(cls, v: int) -> int:
        """Validate cache max size.

        Args:
            v: Cache max size value

        Returns:
            Validated value

        Raises:
            ValueError: If value is too large
        """
        if v > 1000000:
            raise ValueError("Cache max size cannot exceed 1,000,000")
        return v

    @field_validator("CACHE_TTL")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL.

        Args:
            v: Cache TTL value

        Returns:
            Validated value

        Raises:
            ValueError: If value is too large
        """
        if v > 86400:  # 24 hours
            raise ValueError("Cache TTL cannot exceed 24 hours")
        return v
