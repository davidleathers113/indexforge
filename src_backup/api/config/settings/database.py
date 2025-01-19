"""Database and caching settings configuration."""

from pydantic import Field, field_validator

from src.api.config.settings import BaseAppSettings


class DatabaseSettings(BaseAppSettings):
    """Database and caching settings."""

    # Database Configuration
    DB_POOL_SIZE: int = Field(default=20, ge=5, le=100, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum number of connections that can be created beyond pool_size",
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Seconds to wait before giving up on getting a connection from the pool",
    )
    DB_ECHO: bool = Field(default=False, description="Enable SQL query logging")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis server host")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535, description="Redis server port")

    # Cache Settings
    CACHE_TTL: int = Field(default=3600, ge=1, le=86400, description="Default cache TTL in seconds")
    CACHE_MAX_MEMORY: str = Field(default="1gb", description="Maximum memory for cache")
    CACHE_POLICY: str = Field(default="allkeys-lru", description="Cache eviction policy")

    @field_validator("CACHE_MAX_MEMORY")
    @classmethod
    def validate_cache_memory(cls, v: str) -> str:
        """Validate cache memory format."""
        units = {"kb", "mb", "gb"}
        value = v.lower()
        if not any(value.endswith(unit) for unit in units):
            raise ValueError(f"CACHE_MAX_MEMORY must end with one of {units}")
        try:
            size = float(value[:-2])
            if size <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("CACHE_MAX_MEMORY must be a positive number followed by kb, mb, or gb")
        return v

    @field_validator("CACHE_POLICY")
    @classmethod
    def validate_cache_policy(cls, v: str) -> str:
        """Validate cache policy."""
        allowed_policies = {
            "allkeys-lru",
            "volatile-lru",
            "allkeys-random",
            "volatile-random",
            "volatile-ttl",
        }
        if v not in allowed_policies:
            raise ValueError(f"CACHE_POLICY must be one of {allowed_policies}")
        return v
