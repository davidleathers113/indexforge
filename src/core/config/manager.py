"""Configuration management for IndexForge.

This module provides the configuration manager responsible for loading,
caching, and managing environment-specific configuration settings.
"""

import datetime
import json
import os
from pathlib import Path
from typing import TypeVar

from src.core.schema.base import (
    BaseConfiguration,
    ConfigurationError,
    ConfigurationMigration,
    ConfigurationSource,
    ConfigurationVersion,
    MigrationError,
)
from src.core.security.encryption import EncryptionManager


T = TypeVar("T", bound=BaseConfiguration)


class ConfigurationManager:
    """Manager for handling configuration loading and caching."""

    def __init__(
        self,
        config_dir: str | Path | None = None,
        encryption_manager: EncryptionManager | None = None,
    ):
        """Initialize configuration manager.

        Args:
            config_dir: Optional directory for configuration files.
                      Defaults to current directory.
            encryption_manager: Optional encryption manager for secure storage.
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self._cache: dict[str, BaseConfiguration] = {}
        self._env = os.getenv("INDEXFORGE_ENV", "development")
        self._migrations: dict[str, list[ConfigurationMigration]] = {}
        self._encryption_manager = encryption_manager

    def register_migration(self, config_name: str, migration: ConfigurationMigration) -> None:
        """Register a migration handler for a configuration type.

        Args:
            config_name: Name of the configuration
            migration: Migration handler to register
        """
        if config_name not in self._migrations:
            self._migrations[config_name] = []
        self._migrations[config_name].append(migration)

    def get_config(
        self,
        config_class: type[T],
        name: str,
        environment: str | None = None,
        reload: bool = False,
        validate: bool = True,
    ) -> T:
        """Get configuration instance.

        Args:
            config_class: Configuration class to instantiate
            name: Configuration name (used for file naming)
            environment: Optional environment override
            reload: Whether to force reload from disk
            validate: Whether to validate the configuration

        Returns:
            Configuration instance

        Raises:
            ConfigurationError: If loading fails
            MigrationError: If migration fails
        """
        cache_key = f"{name}:{environment or self._env}"

        if not reload and cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, config_class):
                return cached

        config = self._load_config(config_class, name, environment)

        # Perform migrations if needed
        if name in self._migrations:
            config = self._migrate_config(config, name)

        if validate:
            self._validate_config(config)

        self._cache[cache_key] = config
        return config

    def _migrate_config(self, config: T, name: str) -> T:
        """Migrate configuration to latest version.

        Args:
            config: Configuration to migrate
            name: Configuration name

        Returns:
            Migrated configuration

        Raises:
            MigrationError: If migration fails
        """
        current_version = config.version
        target_version = ConfigurationVersion(major=1, minor=0, patch=0)  # Latest version

        if current_version == target_version:
            return config

        migrations = self._migrations.get(name, [])
        data = config.dict()

        try:
            for migration in migrations:
                if migration.can_migrate(current_version, target_version):
                    data = migration.migrate(data, current_version)
                    current_version = target_version

            return config.__class__.parse_obj(data)
        except Exception as e:
            raise MigrationError(
                f"Failed to migrate configuration: {e}",
                str(current_version),
                str(target_version),
            )

    def _validate_config(self, config: BaseConfiguration) -> None:
        """Validate configuration.

        Args:
            config: Configuration to validate

        Raises:
            ConfigurationError: If validation fails
        """
        try:
            # Basic validation (done by pydantic)
            config.dict()

            # Environment-specific validation
            config.validate_for_environment()

            # Validate sensitive fields are properly handled
            if config.sensitive_fields and not self._encryption_manager:
                raise ConfigurationError(
                    "Configuration contains sensitive fields but no encryption manager is configured"
                )
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")

    def _load_config(
        self,
        config_class: type[T],
        name: str,
        environment: str | None = None,
    ) -> T:
        """Load configuration from files and environment.

        The loading process follows this order:
        1. Load base configuration
        2. Load environment-specific overrides
        3. Apply environment variables
        4. Handle sensitive fields

        Args:
            config_class: Configuration class to instantiate
            name: Configuration name
            environment: Optional environment override

        Returns:
            Configuration instance

        Raises:
            ConfigurationError: If loading fails
        """
        env = environment or self._env
        base_path = self.config_dir / f"{name}.yml"
        env_path = self.config_dir / f"{name}.{env}.yml"
        secure_path = self.config_dir / f"{name}.{env}.secure.yml"

        # Load base configuration
        try:
            config = config_class.load(base_path)
        except ConfigurationError:
            if base_path.exists():  # Only re-raise if file exists but loading failed
                raise
            # Create default configuration
            config = config_class(
                version=ConfigurationVersion(major=1, minor=0, patch=0),
                environment=env,
                source=ConfigurationSource.DEFAULT,
            )

        # Load environment overrides
        if env_path.exists():
            try:
                env_config = config_class.load(env_path)
                config = self._merge_configs(config, env_config)
                config.source = ConfigurationSource.FILE
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load environment configuration from {env_path}: {e}"
                )

        # Load secure configuration if encryption manager is available
        if self._encryption_manager and secure_path.exists():
            try:
                encrypted_data = secure_path.read_bytes()
                decrypted_data = self._encryption_manager.decrypt(encrypted_data)
                secure_config = json.loads(decrypted_data)
                config = self._merge_configs(config, config_class.parse_obj(secure_config))
            except Exception as e:
                raise ConfigurationError(f"Failed to load secure configuration: {e}")

        # Apply environment variables
        env_prefix = f"INDEXFORGE_{name.upper()}_"
        config = self._apply_environment_variables(config, env_prefix)

        # Update last modified timestamp
        config.last_modified = datetime.datetime.utcnow().isoformat()

        return config

    def _merge_configs(self, base: T, override: T) -> T:
        """Merge two configurations.

        Args:
            base: Base configuration
            override: Configuration with override values

        Returns:
            Merged configuration
        """
        base_data = base.dict()
        override_data = override.dict()

        # Preserve sensitive fields and overrides
        sensitive_fields = base.sensitive_fields | override.sensitive_fields
        all_overrides = base.overrides.copy()
        all_overrides.update(override.overrides)

        # Merge data
        base_data.update(override_data)

        # Restore preserved fields
        result = base.__class__.parse_obj(base_data)
        result.sensitive_fields = sensitive_fields
        result.overrides = all_overrides

        return result

    def save_config(
        self,
        config: BaseConfiguration,
        name: str,
        environment: str | None = None,
        secure: bool = False,
    ) -> None:
        """Save configuration to file.

        Args:
            config: Configuration instance to save
            name: Configuration name
            environment: Optional environment name
            secure: Whether to save as secure configuration

        Raises:
            ConfigurationError: If saving fails
        """
        env = environment or config.environment

        if secure:
            if not self._encryption_manager:
                raise ConfigurationError(
                    "Cannot save secure configuration without encryption manager"
                )

            path = self.config_dir / f"{name}.{env}.secure.yml"
            try:
                # Only save sensitive fields
                secure_data = {
                    field: getattr(config, field)
                    for field in config.sensitive_fields
                    if hasattr(config, field)
                }
                if secure_data:
                    encrypted_data = self._encryption_manager.encrypt(
                        json.dumps(secure_data).encode()
                    )
                    path.write_bytes(encrypted_data)
            except Exception as e:
                raise ConfigurationError(f"Failed to save secure configuration: {e}")
        else:
            if env == "development":
                path = self.config_dir / f"{name}.yml"
            else:
                path = self.config_dir / f"{name}.{env}.yml"

            # Don't save sensitive fields to non-secure files
            config_data = config.dict(exclude_sensitive=True)
            config_class = config.__class__
            safe_config = config_class.parse_obj(config_data)
            safe_config.save(path)

        # Update cache
        cache_key = f"{name}:{env}"
        self._cache[cache_key] = config

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._cache.clear()
