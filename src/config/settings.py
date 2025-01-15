"""Settings module for application configuration.

This module provides a centralized location for managing application settings
using Pydantic for validation and type safety.
"""

from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    This class uses Pydantic's BaseSettings to manage configuration with environment
    variables and strong type validation.
    """

    # API Settings
    api_title: str = Field(default="IndexForge API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Redis Settings
    redis_url: RedisDsn = Field(..., env="REDIS_URL")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")

    # Weaviate Settings
    weaviate_url: AnyHttpUrl = Field(..., env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(None, env="WEAVIATE_API_KEY")

    # ML Settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    batch_size: int = Field(default=32, env="BATCH_SIZE")

    # Security Settings
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: list[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
