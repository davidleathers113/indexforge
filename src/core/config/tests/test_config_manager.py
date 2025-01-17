"""Tests for the configuration management system.

This module provides comprehensive test coverage for the configuration manager,
including secure storage, migrations, validation, and configuration merging.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest
from pydantic import Field

from src.core.config.manager import ConfigurationManager
from src.core.schema.base import (
    BaseConfiguration,
    ConfigurationError,
    ConfigurationMigration,
    ConfigurationSource,
    ConfigurationVersion,
    MigrationError,
)
from src.core.security.encryption import EncryptionManager


class TestConfig(BaseConfiguration):
    """Test configuration class."""

    name: str = Field(default="test")
    value: int = Field(default=42)
    api_key: Optional[str] = Field(default=None)
    debug: bool = Field(default=False)

    def validate_for_environment(self) -> None:
        """Validate configuration for current environment."""
        if self.environment == "production" and self.debug:
            raise ValueError("Debug mode not allowed in production")


class TestMigrationV1ToV2(ConfigurationMigration):
    """Test migration from v1 to v2."""

    def can_migrate(
        self, from_version: ConfigurationVersion, to_version: ConfigurationVersion
    ) -> bool:
        """Check if this migration can handle the version transition."""
        return (
            from_version.major == 1
            and from_version.minor == 0
            and to_version.major == 2
            and to_version.minor == 0
        )

    def migrate(self, config: Dict[str, Any], from_version: ConfigurationVersion) -> Dict[str, Any]:
        """Migrate configuration from v1 to v2."""
        config["value"] = config.get("value", 0) * 2  # Double the value in v2
        return config


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for configuration files."""
    return tmp_path


@pytest.fixture
def encryption_manager() -> Mock:
    """Create a mock encryption manager."""
    manager = Mock(spec=EncryptionManager)
    manager.encrypt.side_effect = lambda data: b"encrypted:" + data
    manager.decrypt.side_effect = lambda data: data.replace(b"encrypted:", b"")
    return manager


@pytest.fixture
def config_manager(temp_config_dir: Path, encryption_manager: Mock) -> ConfigurationManager:
    """Create a configuration manager instance."""
    return ConfigurationManager(
        config_dir=temp_config_dir,
        encryption_manager=encryption_manager,
    )


def test_init_defaults():
    """Test configuration manager initialization with defaults."""
    manager = ConfigurationManager()
    assert manager.config_dir == Path.cwd()
    assert manager._env == "development"
    assert not manager._migrations
    assert manager._encryption_manager is None


def test_init_with_config_dir(temp_config_dir: Path):
    """Test initialization with custom config directory."""
    manager = ConfigurationManager(config_dir=temp_config_dir)
    assert manager.config_dir == temp_config_dir


def test_register_migration(config_manager: ConfigurationManager):
    """Test migration registration."""
    migration = TestMigrationV1ToV2()
    config_manager.register_migration("test", migration)
    assert len(config_manager._migrations["test"]) == 1
    assert config_manager._migrations["test"][0] is migration


def test_get_config_default(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test getting default configuration when no file exists."""
    config = config_manager.get_config(TestConfig, "test")
    assert isinstance(config, TestConfig)
    assert config.name == "test"
    assert config.value == 42
    assert config.source == ConfigurationSource.DEFAULT


def test_get_config_from_file(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test loading configuration from file."""
    config_path = temp_config_dir / "test.yml"
    config_data = {
        "name": "custom",
        "value": 100,
        "version": {"major": 1, "minor": 0, "patch": 0},
    }

    import yaml

    with config_path.open("w") as f:
        yaml.safe_dump(config_data, f)

    config = config_manager.get_config(TestConfig, "test")
    assert config.name == "custom"
    assert config.value == 100
    assert config.source == ConfigurationSource.FILE


def test_get_config_with_environment(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test loading environment-specific configuration."""
    # Create base config
    base_path = temp_config_dir / "test.yml"
    base_data = {
        "name": "base",
        "value": 100,
        "version": {"major": 1, "minor": 0, "patch": 0},
    }

    # Create prod config
    prod_path = temp_config_dir / "test.production.yml"
    prod_data = {
        "name": "prod",
        "value": 200,
        "version": {"major": 1, "minor": 0, "patch": 0},
    }

    import yaml

    with base_path.open("w") as f:
        yaml.safe_dump(base_data, f)
    with prod_path.open("w") as f:
        yaml.safe_dump(prod_data, f)

    config = config_manager.get_config(TestConfig, "test", environment="production")
    assert config.name == "prod"
    assert config.value == 200
    assert config.environment == "production"


def test_secure_config(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test handling of secure configuration data."""
    # Create a config with sensitive data
    config = TestConfig(
        name="secure_test",
        value=42,
        api_key="secret123",
    )
    config.mark_sensitive("api_key")

    # Save both regular and secure configs
    config_manager.save_config(config, "test", secure=True)
    config_manager.save_config(config, "test")

    # Verify regular config doesn't contain sensitive data
    regular_path = temp_config_dir / "test.yml"
    import yaml

    with regular_path.open("r") as f:
        regular_data = yaml.safe_load(f)
    assert "api_key" not in regular_data

    # Load config and verify sensitive data is present
    loaded_config = config_manager.get_config(TestConfig, "test")
    assert loaded_config.api_key == "secret123"


def test_config_migration(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test configuration migration process."""
    # Register migration
    migration = TestMigrationV1ToV2()
    config_manager.register_migration("test", migration)

    # Create v1 config
    config_path = temp_config_dir / "test.yml"
    config_data = {
        "name": "migrate_test",
        "value": 50,
        "version": {"major": 1, "minor": 0, "patch": 0},
    }

    import yaml

    with config_path.open("w") as f:
        yaml.safe_dump(config_data, f)

    # Load and verify migration
    config = config_manager.get_config(TestConfig, "test")
    assert config.value == 100  # Should be doubled by migration


def test_config_validation(config_manager: ConfigurationManager):
    """Test configuration validation."""
    # Test environment-specific validation
    config = TestConfig(
        name="validation_test",
        debug=True,
        environment="production",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        config_manager._validate_config(config)
    assert "Debug mode not allowed in production" in str(exc_info.value)


def test_config_merging(config_manager: ConfigurationManager):
    """Test configuration merging behavior."""
    base = TestConfig(
        name="base",
        value=100,
        api_key="base_key",
    )
    base.mark_sensitive("api_key")
    base.set_override("value", 150, "staging")

    override = TestConfig(
        name="override",
        value=200,
        api_key="override_key",
    )
    override.mark_sensitive("api_key")
    override.set_override("name", "override_staging", "staging")

    merged = config_manager._merge_configs(base, override)

    # Verify merged values
    assert merged.name == "override"
    assert merged.value == 200
    assert merged.api_key == "override_key"

    # Verify sensitive fields were preserved
    assert "api_key" in merged.sensitive_fields

    # Verify overrides were merged
    assert merged.get_value("value", "staging") == 150
    assert merged.get_value("name", "staging") == "override_staging"


def test_environment_variables(
    config_manager: ConfigurationManager, monkeypatch: pytest.MonkeyPatch
):
    """Test environment variable handling."""
    # Set environment variables
    monkeypatch.setenv("INDEXFORGE_TEST_NAME", "env_name")
    monkeypatch.setenv("INDEXFORGE_TEST_VALUE", "123")
    monkeypatch.setenv("INDEXFORGE_TEST_DEBUG", "true")

    config = config_manager.get_config(TestConfig, "test")

    assert config.name == "env_name"
    assert config.value == 123
    assert config.debug is True
    assert config.source == ConfigurationSource.ENVIRONMENT


def test_cache_behavior(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test configuration caching behavior."""
    # Initial load
    config1 = config_manager.get_config(TestConfig, "test")

    # Should use cache
    config2 = config_manager.get_config(TestConfig, "test")
    assert config1 is config2

    # Force reload
    config3 = config_manager.get_config(TestConfig, "test", reload=True)
    assert config1 is not config3

    # Clear cache
    config_manager.clear_cache()
    config4 = config_manager.get_config(TestConfig, "test")
    assert config1 is not config4


def test_error_handling(config_manager: ConfigurationManager, temp_config_dir: Path):
    """Test error handling in various scenarios."""
    # Test invalid YAML
    config_path = temp_config_dir / "test.yml"
    config_path.write_text("invalid: yaml: content")

    with pytest.raises(ConfigurationError) as exc_info:
        config_manager.get_config(TestConfig, "test")
    assert "Failed to load configuration" in str(exc_info.value)

    # Test migration error
    class FailingMigration(ConfigurationMigration):
        def can_migrate(
            self, from_version: ConfigurationVersion, to_version: ConfigurationVersion
        ) -> bool:
            return True

        def migrate(
            self, config: Dict[str, Any], from_version: ConfigurationVersion
        ) -> Dict[str, Any]:
            raise ValueError("Migration failed")

    config_manager.register_migration("test", FailingMigration())

    with pytest.raises(MigrationError) as exc_info:
        config_manager.get_config(TestConfig, "test")
    assert "Migration failed" in str(exc_info.value)


def test_timestamp_tracking(config_manager: ConfigurationManager):
    """Test last modified timestamp tracking."""
    config = config_manager.get_config(TestConfig, "test")
    assert config.last_modified is not None

    timestamp = datetime.fromisoformat(config.last_modified)
    assert isinstance(timestamp, datetime)
    assert (datetime.utcnow() - timestamp).total_seconds() < 1


def test_secure_storage_requirements(temp_config_dir: Path):
    """Test secure storage requirements."""
    # Create manager without encryption
    manager = ConfigurationManager(config_dir=temp_config_dir)

    config = TestConfig(name="secure_test", api_key="secret")
    config.mark_sensitive("api_key")

    # Should raise error when trying to save secure config without encryption manager
    with pytest.raises(ConfigurationError) as exc_info:
        manager.save_config(config, "test", secure=True)
    assert "encryption manager" in str(exc_info.value)

    # Should raise error when loading config with sensitive fields without encryption manager
    with pytest.raises(ConfigurationError) as exc_info:
        manager._validate_config(config)
    assert "encryption manager" in str(exc_info.value)
