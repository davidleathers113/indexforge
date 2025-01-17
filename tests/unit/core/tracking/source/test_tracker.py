"""Unit tests for source tracking."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.errors import ValidationError
from src.core.schema import Schema, SchemaStorage
from src.core.tracking.source.config import SourceConfig
from src.core.tracking.source.tracker import SourceTracker


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


def test_source_tracker_initialization(temp_config_dir):
    """Test initializing a SourceTracker."""
    tracker = SourceTracker("word", str(temp_config_dir))

    assert tracker.source_type == "word"
    assert tracker.config_dir == temp_config_dir
    assert isinstance(tracker.config, SourceConfig)


def test_source_tracker_default_config(temp_config_dir):
    """Test default configuration creation."""
    tracker = SourceTracker("pdf", str(temp_config_dir))
    config = tracker.config

    assert config.schema_variations["class"] == "PdfDocument"
    assert isinstance(config.custom_properties, dict)
    assert config.vectorizer_settings["model"] == "all-MiniLM-L6-v2"
    assert isinstance(config.cross_source_mappings, dict)


@patch("src.core.tracking.source.tracker.SchemaStorage")
def test_get_schema(mock_storage_class, temp_config_dir):
    """Test getting source-specific schema."""
    mock_storage = mock_storage_class.return_value
    mock_storage.get_schema.return_value = {
        "class": "Document",
        "properties": {"title": {"type": "string"}},
    }

    tracker = SourceTracker("word", str(temp_config_dir))
    schema = tracker.get_schema()

    assert schema["class"] == "WordDocument"  # From schema variations
    assert "title" in schema["properties"]  # From base schema


def test_update_config(temp_config_dir):
    """Test updating source configuration."""
    tracker = SourceTracker("excel", str(temp_config_dir))

    updates = {
        "schema_variations": {
            "class": "ExcelWorkbook",
            "description": "Excel workbook source",
        },
        "custom_properties": {
            "sheet_count": {
                "dataType": ["int"],
                "description": "Number of sheets",
            }
        },
    }

    tracker.update_config(updates)

    assert tracker.config.schema_variations["class"] == "ExcelWorkbook"
    assert tracker.config.custom_properties["sheet_count"]["dataType"] == ["int"]

    # Verify config was saved
    config_path = temp_config_dir / "excel_config.json"
    assert config_path.exists()

    with open(config_path) as f:
        saved_config = json.load(f)
        assert saved_config["schema_variations"]["class"] == "ExcelWorkbook"


@patch("src.core.tracking.source.tracker.SchemaStorage")
def test_validate_schema_errors(mock_storage_class, temp_config_dir):
    """Test schema validation with errors."""
    mock_storage = mock_storage_class.return_value
    mock_storage.get_schema.return_value = {
        "class": "Document",
        "properties": {"title": {"type": "string"}},
    }

    tracker = SourceTracker("word", str(temp_config_dir))

    # Add invalid custom property
    tracker.config.custom_properties = {
        "invalid_prop": {
            # Missing dataType and description
        }
    }

    errors = tracker.validate_schema()
    assert len(errors) == 2  # Missing dataType and description
    assert "missing dataType" in errors[0]
    assert "missing description" in errors[1]


def test_load_invalid_config(temp_config_dir):
    """Test loading invalid configuration file."""
    config_path = temp_config_dir / "invalid_config.json"
    with open(config_path, "w") as f:
        f.write("invalid json content")

    tracker = SourceTracker("invalid", str(temp_config_dir))

    # Should fall back to default config
    assert isinstance(tracker.config, SourceConfig)
    assert tracker.config.schema_variations["class"] == "InvalidDocument"
