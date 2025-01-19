"""Centralized settings management for the application."""

from functools import lru_cache

from pydantic import AnyHttpUrl, Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    api_title: str = Field(default="IndexForge API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Service URLs
    redis_url: RedisDsn = Field(..., env="REDIS_URL")
    weaviate_url: AnyHttpUrl = Field(..., env="WEAVIATE_URL")

    # API Keys and Authentication
    weaviate_api_key: str | None = Field(None, env="WEAVIATE_API_KEY")
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: list[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # Redis Configuration
    redis_pool_size: int = Field(default=20, env="REDIS_POOL_SIZE")
    redis_timeout: float = Field(default=5.0, env="REDIS_TIMEOUT")
    redis_retry_attempts: int = Field(default=3, env="REDIS_RETRY_ATTEMPTS")
    redis_retry_delay: float = Field(default=0.1, env="REDIS_RETRY_DELAY")

    # Weaviate Configuration
    weaviate_batch_size: int = Field(default=100, env="WEAVIATE_BATCH_SIZE")
    weaviate_dynamic_batching: bool = Field(default=True, env="WEAVIATE_DYNAMIC_BATCHING")
    weaviate_timeout: float = Field(default=30.0, env="WEAVIATE_TIMEOUT")

    # Performance Settings
    operation_timeout: float = Field(default=30.0, env="OPERATION_TIMEOUT")
    max_concurrent_operations: int = Field(default=100, env="MAX_CONCURRENT_OPERATIONS")
    batch_size: int = Field(default=1000, env="BATCH_SIZE")

    # Resource Management
    max_memory_mb: int = Field(default=1024, env="MAX_MEMORY_MB")
    max_vector_dim: int = Field(default=768, env="MAX_VECTOR_DIM")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")

    # Monitoring and Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_history_size: int = Field(default=5000, env="METRICS_HISTORY_SIZE")
    slow_operation_threshold_ms: float = Field(default=100.0, env="SLOW_OPERATION_THRESHOLD_MS")
    error_threshold_percent: float = Field(default=5.0, env="ERROR_THRESHOLD_PERCENT")

    # Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    overlap_size: int = Field(default=200, env="OVERLAP_SIZE")
    min_chunk_size: int = Field(default=100, env="MIN_CHUNK_SIZE")

    # ML Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    enable_gpu: bool = Field(default=False, env="ENABLE_GPU")

    # Validation Settings
    enable_strict_validation: bool = Field(default=True, env="ENABLE_STRICT_VALIDATION")
    max_validation_retries: int = Field(default=3, env="MAX_VALIDATION_RETRIES")
    validation_timeout: float = Field(default=5.0, env="VALIDATION_TIMEOUT")

    # Health Check Configuration
    health_check_interval: float = Field(default=60.0, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: float = Field(default=5.0, env="HEALTH_CHECK_TIMEOUT")
    unhealthy_threshold: int = Field(default=3, env="UNHEALTHY_THRESHOLD")

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    def get_api_config(self) -> dict:
        """Get API-specific configuration."""
        return {
            "title": self.api_title,
            "version": self.api_version,
            "debug": self.debug,
            "secret_key": self.secret_key,
            "allowed_hosts": self.allowed_hosts,
        }

    def get_redis_config(self) -> dict:
        """Get Redis-specific configuration."""
        return {
            "url": self.redis_url,
            "pool_size": self.redis_pool_size,
            "timeout": self.redis_timeout,
            "retry_attempts": self.redis_retry_attempts,
            "retry_delay": self.redis_retry_delay,
        }

    def get_weaviate_config(self) -> dict:
        """Get Weaviate-specific configuration."""
        return {
            "url": self.weaviate_url,
            "api_key": self.weaviate_api_key,
            "batch_size": self.weaviate_batch_size,
            "timeout": self.weaviate_timeout,
            "dynamic_batching": self.weaviate_dynamic_batching,
        }

    def get_performance_config(self) -> dict:
        """Get performance-related configuration."""
        return {
            "operation_timeout": self.operation_timeout,
            "max_concurrent_operations": self.max_concurrent_operations,
            "batch_size": self.batch_size,
            "max_memory_mb": self.max_memory_mb,
        }

    def get_metrics_config(self) -> dict:
        """Get metrics-related configuration."""
        return {
            "enable_metrics": self.enable_metrics,
            "history_size": self.metrics_history_size,
            "slow_threshold_ms": self.slow_operation_threshold_ms,
            "error_threshold": self.error_threshold_percent,
        }

    def get_processing_config(self) -> dict:
        """Get text processing configuration."""
        return {
            "chunk_size": self.chunk_size,
            "overlap_size": self.overlap_size,
            "min_chunk_size": self.min_chunk_size,
            "embedding_model": self.embedding_model,
            "embedding_batch_size": self.embedding_batch_size,
            "enable_gpu": self.enable_gpu,
        }

    def get_validation_config(self) -> dict:
        """Get validation-related configuration."""
        return {
            "strict_validation": self.enable_strict_validation,
            "max_retries": self.max_validation_retries,
            "timeout": self.validation_timeout,
        }

    def get_health_check_config(self) -> dict:
        """Get health check configuration."""
        return {
            "interval": self.health_check_interval,
            "timeout": self.health_check_timeout,
            "unhealthy_threshold": self.unhealthy_threshold,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
