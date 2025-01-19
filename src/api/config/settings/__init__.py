"""Settings module."""

from functools import lru_cache

from .api import APISettings
from .base import BaseAppSettings
from .database import DatabaseSettings
from .monitoring import MonitoringSettings
from .performance import PerformanceSettings
from .security import SecuritySettings
from .weaviate import WeaviateSettings


class Settings(BaseAppSettings):
    """Main settings class that composes all settings modules."""

    api: APISettings = APISettings()
    database: DatabaseSettings = DatabaseSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    performance: PerformanceSettings = PerformanceSettings()
    security: SecuritySettings = SecuritySettings()
    weaviate: WeaviateSettings = WeaviateSettings()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()


__all__ = ["Settings", "get_settings"]
