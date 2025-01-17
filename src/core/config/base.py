"""Base configuration management for IndexForge.

This module provides the core configuration management functionality, including:
- Configuration schema definition and validation
- Configuration persistence and loading
- Version tracking and migration support
- Environment-specific configuration handling
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator
from typing_extensions import Protocol


class ConfigurationSource(str, Enum):
    """Source of configuration values."""

    FILE = "file"
    ENVIRONMENT = "environment"
    DEFAULT = "default"
    OVERRIDE = "override"


class ConfigurationError(Exception):
    """Base class for configuration-related errors."""

    pass


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        self.details = details or {}
        super().__init__(message)


class MigrationError(ConfigurationError):
    """Raised when configuration migration fails."""

    def __init__(self, message: str, from_version: str, to_version: str):
        self.from_version = from_version
        self.to_version = to_version
        super().__init__(f"{message} (from {from_version} to {to_version})")


class ConfigurationVersion(BaseModel):
    """Configuration version information."""

    major: int = Field(..., description="Major version number")
    minor: int = Field(..., description="Minor version number")
    patch: int = Field(..., description="Patch version number")

    @validator("major", "minor", "patch")
    def validate_version_numbers(self, v: int) -> int:
        """Validate version numbers are non-negative."""
        if v < 0:
            raise ValueError("Version numbers must be non-negative")
        return v

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "ConfigurationVersion") -> bool:
        """Check if this version is less than another version."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


class ConfigurationMigration(Protocol):
    """Protocol for configuration migration handlers."""

    def can_migrate(
        self, from_version: ConfigurationVersion, to_version: ConfigurationVersion
    ) -> bool:
        """Check if this migration can handle the version transition."""
        ...

    def migrate(self, config: Dict[str, Any], from_version: ConfigurationVersion) -> Dict[str, Any]:
        """Migrate configuration from one version to another."""
        ...


class BaseConfiguration(BaseModel):
    """Base class for all configuration objects."""

    version: ConfigurationVersion = Field(
        default_factory=lambda: ConfigurationVersion(major=1, minor=0, patch=0),
        description="Configuration version",
    )
    source: ConfigurationSource = Field(
        default=ConfigurationSource.DEFAULT,
        description="Source of configuration values",
    )
    environment: str = Field(
        default="development",
        description="Environment this configuration is for",
    )
    tenant_id: Optional[UUID] = Field(
        default=None,
        description="Optional tenant ID for multi-tenant configurations",
    )
    last_modified: Optional[str] = Field(
        default=None,
        description="ISO format timestamp of last modification",
    )
    overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Environment-specific value overrides",
    )
    sensitive_fields: Set[str] = Field(
        default_factory=set,
        description="Fields containing sensitive information",
    )

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
        json_encoders = {UUID: str}
        extra = "forbid"

    def get_value(self, field_name: str, environment: Optional[str] = None) -> Any:
        """Get potentially overridden configuration value."""
        env = environment or self.environment
        override_key = f"{field_name}:{env}"
        return self.overrides.get(override_key, getattr(self, field_name))

    def set_override(self, field_name: str, value: Any, environment: str) -> None:
        """Set environment-specific override value."""
        if field_name not in self.__fields__:
            raise ValueError(f"Unknown field: {field_name}")
        override_key = f"{field_name}:{environment}"
        self.overrides[override_key] = value

    def remove_override(self, field_name: str, environment: str) -> None:
        """Remove environment-specific override value."""
        override_key = f"{field_name}:{environment}"
        self.overrides.pop(override_key, None)

    def mark_sensitive(self, field_name: str) -> None:
        """Mark a field as containing sensitive information."""
        if field_name not in self.__fields__:
            raise ValueError(f"Unknown field: {field_name}")
        self.sensitive_fields.add(field_name)

    def is_sensitive(self, field_name: str) -> bool:
        """Check if a field contains sensitive information."""
        return field_name in self.sensitive_fields

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict serialization to handle sensitive fields."""
        exclude_sensitive = kwargs.pop("exclude_sensitive", False)
        data = super().dict(*args, **kwargs)

        if exclude_sensitive:
            for field in self.sensitive_fields:
                if field in data:
                    data[field] = "***REDACTED***"

        return data

    @classmethod
    def load(cls, path: Union[str, Path]) -> "BaseConfiguration":
        """Load configuration from a file.

        Args:
            path: Path to configuration file

        Returns:
            Loaded configuration instance

        Raises:
            ConfigurationError: If loading fails
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {path}")

            import yaml

            with path.open("r") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ConfigurationError("Invalid configuration format")

            return cls.parse_obj(data)
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save(self, path: Union[str, Path]) -> None:
        """Save configuration to a file.

        Args:
            path: Path to save configuration to

        Raises:
            ConfigurationError: If saving fails
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            import yaml

            with path.open("w") as f:
                yaml.safe_dump(
                    self.dict(exclude_none=True), f, default_flow_style=False, sort_keys=False
                )
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def merge_with(self, other: "BaseConfiguration") -> "BaseConfiguration":
        """Merge this configuration with another one.

        The other configuration takes precedence for any overlapping fields.

        Args:
            other: Another configuration to merge with

        Returns:
            New configuration instance with merged values

        Raises:
            ConfigurationError: If configurations are incompatible
        """
        if not isinstance(other, self.__class__):
            raise ConfigurationError(
                f"Cannot merge with configuration of different type: {type(other)}"
            )

        if not self.version.is_compatible_with(other.version):
            raise ConfigurationError(
                f"Incompatible configuration versions: {self.version} vs {other.version}"
            )

        # Create new instance with merged values
        merged_data = self.dict(exclude_none=True)
        merged_data.update(other.dict(exclude_none=True))

        return self.__class__.parse_obj(merged_data)

    def validate_for_environment(self) -> None:
        """Validate configuration for current environment.

        This method should be overridden by subclasses to add
        environment-specific validation rules.

        Raises:
            ValidationError: If validation fails
        """
        pass
