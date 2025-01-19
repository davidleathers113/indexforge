"""Configuration management for IndexForge.

This package provides configuration management utilities and base classes for:
- Configuration loading and validation
- Environment-specific settings
- Configuration file handling
"""

from .base import BaseConfiguration, ConfigurationError, ConfigurationSource, ValidationError
from .manager import ConfigurationManager


__all__ = [
    "BaseConfiguration",
    "ConfigurationError",
    "ConfigurationManager",
    "ConfigurationSource",
    "ValidationError",
]
