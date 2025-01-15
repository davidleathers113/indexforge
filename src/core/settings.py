"""Core settings module.

This module provides centralized configuration management using Pydantic
for validation and type safety.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    This class uses Pydantic's BaseSettings to manage configuration with environment
    variables and strong type validation.
    """

    # API Settings
    api_title: str = "IndexForge API"
    api_version: str = "1.0.0"
    debug: bool = False

    # Redis Settings
    redis_url: str
    redis_pool_size: int = 10

    # Weaviate Settings
    weaviate_url: str
    weaviate_api_key: Optional[str] = None

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
