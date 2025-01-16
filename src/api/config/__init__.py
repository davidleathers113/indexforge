"""Config package."""

from .settings import get_settings


settings = get_settings()

__all__ = ["get_settings", "settings"]
