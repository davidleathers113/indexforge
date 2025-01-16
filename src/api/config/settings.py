"""Main settings configuration."""

from functools import lru_cache

from src.api.config.api import APISettings
from src.api.config.cache import CacheSettings
from src.api.config.database import DatabaseSettings
from src.api.config.monitoring import MonitoringSettings
from src.api.config.performance import PerformanceSettings
from src.api.config.security import SecuritySettings
from src.api.config.weaviate import WeaviateSettings


class Settings:
    """Main settings class that composes all settings modules."""

    def __init__(self):
        """Initialize settings."""
        self.api = APISettings()
        self.cache = CacheSettings()
        self.database = DatabaseSettings()
        self.monitoring = MonitoringSettings()
        self.performance = PerformanceSettings()
        self.security = SecuritySettings()
        self.weaviate = WeaviateSettings()

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()
