"""Alert configuration validation.

This module provides validation logic for alert configuration settings.
"""

from dataclasses import fields
from typing import Any


class ConfigValidator:
    """Validator for alert configuration settings."""

    # Class-level constants
    MAX_THRESHOLD: float = 100.0
    MIN_THRESHOLD: float = 0.0
    MIN_COOLDOWN: int = 60
    MIN_RETRIES: int = 1
    MIN_DELAY: int = 1

    @classmethod
    def validate_thresholds(cls, config: Any) -> None:
        """Validate all threshold values in configuration.

        Args:
            config: Configuration object to validate

        Raises:
            ValueError: If any threshold is invalid
        """
        for field in fields(config):
            if not field.name.endswith("_threshold"):
                continue

            value = getattr(config, field.name)
            if not isinstance(value, (int, float)):
                continue

            if not cls.MIN_THRESHOLD <= value <= cls.MAX_THRESHOLD:
                raise ValueError(
                    f"Threshold {field.name} must be between "
                    f"{cls.MIN_THRESHOLD} and {cls.MAX_THRESHOLD}"
                )

    @classmethod
    def validate_timing(cls, cooldown: int, retries: int, delay: int) -> None:
        """Validate timing-related settings.

        Args:
            cooldown: Alert cooldown period in seconds
            retries: Maximum number of retries
            delay: Delay between retries in seconds

        Raises:
            ValueError: If any timing setting is invalid
        """
        if cooldown < cls.MIN_COOLDOWN:
            raise ValueError(f"Alert cooldown must be at least {cls.MIN_COOLDOWN} seconds")
        if retries < cls.MIN_RETRIES:
            raise ValueError("Maximum retries must be at least 1")
        if delay < cls.MIN_DELAY:
            raise ValueError("Retry delay must be at least 1 second")
