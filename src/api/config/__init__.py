"""Config package."""

from .settings import Settings, get_settings

settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
