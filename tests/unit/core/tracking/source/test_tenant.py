"""Unit tests for tenant-specific source tracking."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.errors import ValidationError
from src.core.schema import Schema, SchemaStorage
from src.core.tracking.source.config import SourceConfig
from src.core.tracking.source.tenant import TenantSourceTracker


@pytest.fixture
def mock_schema_storage():
    """Create a mock schema storage."""
    storage = MagicMock(spec=SchemaStorage)
    storage.get_schema.return_value = {
        "class": "Document",
        "description": "Base document schema",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
    }
    return storage


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


def test_tenant_tracker_initialization(temp_config_dir):
    """Test initializing a TenantSourceTracker."""
    tracker = TenantSourceTracker("tenant123", "word", str(temp_config_dir))

    assert tracker.tenant_id == "tenant123"
    assert tracker.source_type == "word"
    assert tracker.config_dir == temp_config_dir / "tenants" / "tenant123"
    assert isinstance(tracker.config, SourceConfig)


def test_tenant_default_config(temp_config_dir):
    """Test tenant-specific default configuration."""
    tracker = TenantSourceTracker("tenant456", "pdf", str(temp_config_dir))
    config = tracker.config

    assert config.schema_variations["tenant_id"] == "tenant456"
    assert config.schema_variations["class"] == "TenantPdfDocument"
    assert "Tenant-specific pdf document" in config.schema_variations["description"].lower()


def test_tenant_config_isolation(temp_config_dir):
    """Test configuration isolation between tenants."""
    tracker1 = TenantSourceTracker("tenant1", "word", str(temp_config_dir))
    tracker2 = TenantSourceTracker("tenant2", "word", str(temp_config_dir))

    # Update first tenant's config
    tracker1.update_config(
        {"schema_variations": {"class": "CustomWord", "description": "Tenant 1 Word"}}
    )

    # Verify second tenant's config is unchanged
    assert tracker2.config.schema_variations["class"] == "TenantWordDocument"
    assert tracker1.config.schema_variations["tenant_id"] == "tenant1"
    assert tracker2.config.schema_variations["tenant_id"] == "tenant2"


def test_tenant_schema_validation(temp_config_dir):
    """Test tenant-specific schema validation."""
    tracker = TenantSourceTracker("tenant789", "excel", str(temp_config_dir))

    # Try to update with invalid tenant_id
    with pytest.raises(ValidationError) as exc_info:
        tracker.update_config({"schema_variations": {"tenant_id": "different_tenant"}})
    assert "Cannot change tenant_id" in str(exc_info.value)

    # Verify tenant_id is preserved
    assert tracker.config.schema_variations["tenant_id"] == "tenant789"


def test_get_tenant_info(temp_config_dir):
    """Test retrieving tenant information."""
    tracker = TenantSourceTracker("tenant_test", "word", str(temp_config_dir))
    info = tracker.get_tenant_info()

    assert info["tenant_id"] == "tenant_test"
    assert info["source_type"] == "word"
    assert str(temp_config_dir / "tenants" / "tenant_test") in info["config_dir"]
    assert info["schema_variations"]["tenant_id"] == "tenant_test"
    assert isinstance(info["custom_properties"], dict)


@patch("src.core.tracking.source.tracker.SchemaStorage")
def test_tenant_schema_inheritance(mock_storage_class, temp_config_dir):
    """Test tenant schema inherits from base schema."""
    mock_storage = mock_storage_class.return_value
    mock_storage.get_schema.return_value = {
        "class": "Document",
        "properties": {"title": {"type": "string"}},
    }

    tracker = TenantSourceTracker("tenant_inherit", "word", str(temp_config_dir))
    schema = tracker.get_schema()

    assert schema["class"] == "TenantWordDocument"  # From tenant variations
    assert "title" in schema["properties"]  # From base schema
    assert schema["tenant_id"] == "tenant_inherit"  # Tenant-specific


def test_tenant_config_persistence(temp_config_dir):
    """Test tenant configuration persistence."""
    tracker = TenantSourceTracker("tenant_persist", "excel", str(temp_config_dir))

    updates = {
        "schema_variations": {"class": "CustomExcel", "description": "Custom Excel format"},
        "custom_properties": {
            "sheet_count": {"dataType": ["int"], "description": "Number of sheets"}
        },
    }

    tracker.update_config(updates)

    # Create new tracker instance to test loading
    new_tracker = TenantSourceTracker("tenant_persist", "excel", str(temp_config_dir))

    assert new_tracker.config.schema_variations["class"] == "CustomExcel"
    assert new_tracker.config.custom_properties["sheet_count"]["dataType"] == ["int"]
    assert new_tracker.config.schema_variations["tenant_id"] == "tenant_persist"
