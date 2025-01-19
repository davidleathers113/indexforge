"""Unit tests for configuration manager."""

import os
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel, Field
import pytest

from src.core.schema.base import (
    BaseConfiguration,
    ConfigurationError,
    ConfigurationSource,
    ConfigurationVersion,
)


class TestConfig(BaseConfiguration):
    """Test configuration class."""

    class Settings(BaseModel):
        """Test settings."""

        host: str = Field(default="localhost")
        port: int = Field(default=8000)
        debug: bool = Field(default=False)

    settings: Settings = Field(default_factory=Settings)


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    return tmp_path


@pytest.fixture
def config_manager(config_dir: Path):
    """Create configuration manager instance."""
    from src.core.config.manager import ConfigurationManager

    return ConfigurationManager(config_dir=config_dir)


def test_get_config_default(config_manager):
    """Test getting default configuration."""
    config = config_manager.get_config(TestConfig, "test")

    assert isinstance(config, TestConfig)
    assert config.version == ConfigurationVersion(major=1, minor=0, patch=0)
    assert config.environment == "development"
    assert config.source == ConfigurationSource.DEFAULT
    assert config.settings.host == "localhost"
    assert config.settings.port == 8000
    assert config.settings.debug is False


def test_get_config_from_file(config_manager, config_dir):
    """Test loading configuration from file."""
    # Create test config file
    config_path = config_dir / "test.yml"
    config_path.write_text(
        """
version:
  major: 2
  minor: 1
  patch: 0
environment: development
settings:
  host: test.local
  port: 9000
  debug: true
"""
    )

    config = config_manager.get_config(TestConfig, "test")

    assert isinstance(config, TestConfig)
    assert config.version == ConfigurationVersion(major=2, minor=1, patch=0)
    assert config.environment == "development"
    assert config.source == ConfigurationSource.FILE
    assert config.settings.host == "test.local"
    assert config.settings.port == 9000
    assert config.settings.debug is True


def test_get_config_environment_override(config_manager, config_dir):
    """Test loading configuration with environment override."""
    # Create base config
    base_path = config_dir / "test.yml"
    base_path.write_text(
        """
version:
  major: 1
  minor: 0
  patch: 0
environment: development
settings:
  host: localhost
  port: 8000
  debug: false
"""
    )

    # Create production config
    prod_path = config_dir / "test.production.yml"
    prod_path.write_text(
        """
version:
  major: 1
  minor: 0
  patch: 0
environment: production
settings:
  host: prod.server
  port: 443
  debug: false
"""
    )

    config = config_manager.get_config(TestConfig, "test", environment="production")

    assert isinstance(config, TestConfig)
    assert config.environment == "production"
    assert config.source == ConfigurationSource.FILE
    assert config.settings.host == "prod.server"
    assert config.settings.port == 443
    assert config.settings.debug is False


def test_get_config_env_vars(config_manager):
    """Test configuration override with environment variables."""
    with patch.dict(
        os.environ,
        {
            "INDEXFORGE_TEST_SETTINGS_HOST": "env.server",
            "INDEXFORGE_TEST_SETTINGS_PORT": "8443",
            "INDEXFORGE_TEST_SETTINGS_DEBUG": "true",
        },
    ):
        config = config_manager.get_config(TestConfig, "test")

        assert isinstance(config, TestConfig)
        assert config.source == ConfigurationSource.ENVIRONMENT
        assert config.settings.host == "env.server"
        assert config.settings.port == 8443
        assert config.settings.debug is True


def test_get_config_cache(config_manager):
    """Test configuration caching."""
    config1 = config_manager.get_config(TestConfig, "test")
    config2 = config_manager.get_config(TestConfig, "test")

    assert config1 is config2  # Same instance from cache

    config3 = config_manager.get_config(TestConfig, "test", reload=True)
    assert config1 is not config3  # Different instance due to reload


def test_save_config(config_manager, config_dir):
    """Test saving configuration to file."""
    config = TestConfig(
        version=ConfigurationVersion(major=1, minor=0, patch=0),
        environment="development",
        source=ConfigurationSource.DEFAULT,
        settings=TestConfig.Settings(host="save.test", port=9090, debug=True),
    )

    config_manager.save_config(config, "test")

    # Verify file was created
    config_path = config_dir / "test.yml"
    assert config_path.exists()

    # Load and verify content
    loaded = config_manager.get_config(TestConfig, "test", reload=True)
    assert loaded.settings.host == "save.test"
    assert loaded.settings.port == 9090
    assert loaded.settings.debug is True


def test_clear_cache(config_manager):
    """Test clearing configuration cache."""
    config1 = config_manager.get_config(TestConfig, "test")
    config_manager.clear_cache()
    config2 = config_manager.get_config(TestConfig, "test")

    assert config1 is not config2  # Different instance after cache clear


def test_invalid_config_file(config_manager, config_dir):
    """Test handling of invalid configuration file."""
    config_path = config_dir / "test.yml"
    config_path.write_text("invalid: yaml: content")

    with pytest.raises(ConfigurationError):
        config_manager.get_config(TestConfig, "test")
