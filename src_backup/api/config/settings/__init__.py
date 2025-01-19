"""Base settings module."""

import os
from typing import Any, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Base settings class with common configuration."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def _is_test_environment(cls) -> bool:
        """Check if running in test environment."""
        return os.getenv("ENVIRONMENT", "").lower() in ("test", "testing")

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Override dict to include nested settings."""
        base_dict = super().dict(*args, **kwargs)
        for key, value in base_dict.items():
            if isinstance(value, BaseSettings):
                base_dict[key] = value.dict(*args, **kwargs)
        return base_dict
