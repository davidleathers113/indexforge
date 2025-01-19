"""Tests for pipeline configuration settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from .settings import CacheConfig, PipelineConfig, ProcessingConfig, RetryConfig


def test_default_config():
    """Test default configuration values."""
    config = PipelineConfig()
    assert config.export_dir == Path("exports")
    assert config.log_dir == Path("logs")
    assert config.index_url == "http://localhost:8080"
    assert config.class_name == "Document"

    # Test component configs
    assert config.processing.batch_size == 100
    assert config.cache.host == "localhost"
    assert config.retry.max_retries == 3


def test_custom_config():
    """Test custom configuration values."""
    config = PipelineConfig(
        export_dir="custom_exports",
        processing=ProcessingConfig(batch_size=200),
        cache=CacheConfig(host="redis.local"),
        retry=RetryConfig(max_retries=5),
    )
    assert config.export_dir == Path("custom_exports")
    assert config.processing.batch_size == 200
    assert config.cache.host == "redis.local"
    assert config.retry.max_retries == 5


def test_env_vars(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("PIPELINE_EXPORT_DIR", "env_exports")
    monkeypatch.setenv("PIPELINE_PROCESSING_BATCH_SIZE", "300")
    monkeypatch.setenv("PIPELINE_CACHE_HOST", "redis.env")

    config = PipelineConfig()
    assert config.export_dir == Path("env_exports")
    assert config.processing.batch_size == 300
    assert config.cache.host == "redis.env"


def test_validation_errors():
    """Test configuration validation."""
    # Test invalid batch size
    with pytest.raises(ValidationError, match="batch_size"):
        ProcessingConfig(batch_size=0)

    # Test invalid document length
    with pytest.raises(ValidationError, match="max_document_length"):
        ProcessingConfig(min_document_length=1000, max_document_length=500)

    # Test invalid port number
    with pytest.raises(ValidationError, match="port"):
        CacheConfig(port=70000)

    # Test invalid retry settings
    with pytest.raises(ValidationError, match="backoff_factor"):
        RetryConfig(backoff_factor=-1)


def test_directory_creation():
    """Test directory creation and validation."""
    test_dir = Path("test_exports")
    try:
        config = PipelineConfig(export_dir=test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert config.export_dir == test_dir
    finally:
        if test_dir.exists():
            test_dir.rmdir()


def test_nested_config_validation():
    """Test validation of nested configuration objects."""
    with pytest.raises(ValidationError) as exc_info:
        PipelineConfig(
            processing={"batch_size": -1},  # Invalid batch size
            cache={"port": 70000},  # Invalid port
        )
    errors = exc_info.value.errors()
    assert len(errors) >= 2  # At least two validation errors
