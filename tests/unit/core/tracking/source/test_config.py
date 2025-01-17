"""Unit tests for source configuration."""

import pytest

from src.core.tracking.source.config import SourceConfig


def test_source_config_creation():
    """Test creating a SourceConfig instance."""
    config = SourceConfig(
        schema_variations={
            "class": "PDFDocument",
            "description": "PDF document source",
        },
        custom_properties={
            "page_count": {
                "dataType": ["int"],
                "description": "Number of pages",
            }
        },
        vectorizer_settings={
            "model": "all-MiniLM-L6-v2",
            "poolingStrategy": "mean",
        },
        cross_source_mappings={
            "word": "document_id",
            "excel": "sheet_id",
        },
    )

    assert config.schema_variations["class"] == "PDFDocument"
    assert config.custom_properties["page_count"]["dataType"] == ["int"]
    assert config.vectorizer_settings["model"] == "all-MiniLM-L6-v2"
    assert config.cross_source_mappings["word"] == "document_id"


def test_source_config_empty_dicts():
    """Test creating a SourceConfig with empty dictionaries."""
    config = SourceConfig(
        schema_variations={},
        custom_properties={},
        vectorizer_settings={},
        cross_source_mappings={},
    )

    assert isinstance(config.schema_variations, dict)
    assert isinstance(config.custom_properties, dict)
    assert isinstance(config.vectorizer_settings, dict)
    assert isinstance(config.cross_source_mappings, dict)
    assert len(config.schema_variations) == 0
    assert len(config.custom_properties) == 0
    assert len(config.vectorizer_settings) == 0
    assert len(config.cross_source_mappings) == 0
