"""Unit tests for text processing configuration.

Tests the validation and functionality of text processing configuration settings.
"""

import pytest
from pydantic import ValidationError

from src.ml.processing.text.config import TextProcessingConfig


def test_default_config():
    """Test default configuration initialization."""
    config = TextProcessingConfig()
    assert config.strip_whitespace is True
    assert config.normalize_unicode is True
    assert config.max_chunk_size > 0
    assert config.chunk_overlap >= 0
    assert config.detect_language is False
    assert config.min_confidence > 0
    assert config.encoding == "utf-8"


def test_custom_config():
    """Test custom configuration initialization."""
    config = TextProcessingConfig(
        strip_whitespace=False,
        normalize_unicode=False,
        max_chunk_size=1000,
        chunk_overlap=100,
        detect_language=True,
        min_confidence=0.8,
        encoding="ascii",
    )
    assert config.strip_whitespace is False
    assert config.normalize_unicode is False
    assert config.max_chunk_size == 1000
    assert config.chunk_overlap == 100
    assert config.detect_language is True
    assert config.min_confidence == 0.8
    assert config.encoding == "ascii"


def test_invalid_chunk_size():
    """Test validation of invalid chunk size."""
    with pytest.raises(ValidationError, match="max_chunk_size"):
        TextProcessingConfig(max_chunk_size=0)

    with pytest.raises(ValidationError, match="max_chunk_size"):
        TextProcessingConfig(max_chunk_size=-1)


def test_invalid_overlap():
    """Test validation of invalid chunk overlap."""
    with pytest.raises(ValidationError, match="chunk_overlap"):
        TextProcessingConfig(max_chunk_size=100, chunk_overlap=-1)

    with pytest.raises(ValidationError, match="chunk_overlap"):
        TextProcessingConfig(max_chunk_size=100, chunk_overlap=101)


def test_invalid_confidence():
    """Test validation of invalid confidence threshold."""
    with pytest.raises(ValidationError, match="min_confidence"):
        TextProcessingConfig(min_confidence=0)

    with pytest.raises(ValidationError, match="min_confidence"):
        TextProcessingConfig(min_confidence=1.1)


def test_invalid_encoding():
    """Test validation of invalid encoding."""
    with pytest.raises(ValidationError, match="encoding"):
        TextProcessingConfig(encoding="invalid")


def test_config_dict():
    """Test configuration to dictionary conversion."""
    config = TextProcessingConfig(max_chunk_size=500, chunk_overlap=50)
    config_dict = config.model_dump()
    assert isinstance(config_dict, dict)
    assert config_dict["max_chunk_size"] == 500
    assert config_dict["chunk_overlap"] == 50


def test_config_json():
    """Test configuration JSON serialization."""
    config = TextProcessingConfig()
    json_str = config.model_dump_json()
    assert isinstance(json_str, str)
    assert "max_chunk_size" in json_str
    assert "chunk_overlap" in json_str


def test_config_copy():
    """Test configuration copy functionality."""
    config1 = TextProcessingConfig(max_chunk_size=500)
    config2 = config1.model_copy()

    assert config1.max_chunk_size == config2.max_chunk_size
    assert id(config1) != id(config2)  # Different objects
