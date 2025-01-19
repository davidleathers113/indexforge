"""Configuration validation models.

This module provides Pydantic models for validating configuration settings
across different components of the application. It ensures type safety and
validation for critical configuration parameters.
"""

import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


class ConnectionSettings(BaseModel):
    """Base connection settings with common validation."""

    max_retries: int = Field(
        default=3, ge=1, le=10, description="Maximum number of connection retry attempts"
    )
    timeout: float = Field(default=30.0, ge=1.0, description="Connection timeout in seconds")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")

    @validator("timeout")
    def validate_timeout(self, v: float) -> float:
        """Ensure timeout is within reasonable bounds."""
        if v > 300:  # 5 minutes max
            raise ValueError("Timeout cannot exceed 300 seconds")
        return v


class DatabaseSettings(ConnectionSettings):
    """Database connection settings with validation."""

    url: str = Field(..., description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_recycle: int = Field(default=3600, ge=0, description="Connection recycle time in seconds")
    max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum number of connections that can be created beyond pool_size",
    )

    @validator("url")
    def validate_database_url(self, v: str) -> str:
        """Validate database URL format and components."""
        parsed = urlparse(v)
        if not all([parsed.scheme, parsed.hostname]):
            raise ValueError("Invalid database URL format")
        if parsed.scheme not in ["postgresql", "mysql", "sqlite"]:
            raise ValueError(f"Unsupported database type: {parsed.scheme}")
        return v


class CacheSettings(ConnectionSettings):
    """Cache configuration settings."""

    ttl: int = Field(default=3600, ge=0, description="Default cache TTL in seconds")
    max_memory: str = Field(default="1gb", description="Maximum memory allocation")
    eviction_policy: str = Field(default="allkeys-lru", description="Cache eviction policy")

    @validator("max_memory")
    def validate_max_memory(self, v: str) -> str:
        """Validate memory specification format."""
        if not re.match(r"^\d+[kmgt]b$", v.lower()):
            raise ValueError("Invalid memory format. Use format: <number><unit>b (kb,mb,gb,tb)")
        return v.lower()

    @validator("eviction_policy")
    def validate_eviction_policy(self, v: str) -> str:
        """Validate cache eviction policy."""
        valid_policies = {
            "allkeys-lru",
            "allkeys-random",
            "volatile-lru",
            "volatile-random",
            "volatile-ttl",
        }
        if v not in valid_policies:
            raise ValueError(
                f"Invalid eviction policy. Must be one of: {', '.join(valid_policies)}"
            )
        return v


class SecuritySettings(BaseModel):
    """Security-related configuration settings."""

    secret_key: str = Field(
        ..., min_length=32, description="Secret key for cryptographic operations"
    )
    enable_csrf: bool = Field(default=True, description="Enable CSRF protection")
    allowed_hosts: list[str] = Field(default=["localhost"], description="List of allowed hosts")

    @validator("secret_key")
    def validate_secret_key(self, v: str) -> str:
        """Validate secret key strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Secret key must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Secret key must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Secret key must contain at least one number")
        return v
