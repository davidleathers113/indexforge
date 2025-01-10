"""Tests for metadata validation edge cases."""

import pytest


def test_handles_empty_metadata(validator, valid_document):
    """Test validation of empty metadata dictionary."""
    valid_document["metadata"] = {}
    result = validator.process(valid_document)
    assert result["metadata"] == {}


def test_handles_none_values(validator, valid_document):
    """Test validation of metadata with None values."""
    valid_document["metadata"] = {"null_value": None, "valid_value": "test"}
    result = validator.process(valid_document)
    assert result["metadata"]["null_value"] is None


def test_rejects_nested_structures(validator, valid_document):
    """Test validation of nested data structures in metadata."""
    valid_document["metadata"] = {
        "nested_dict": {"key": "value"},
        "nested_list": [1, 2, 3],
        "nested_tuple": (1, 2, 3),
    }

    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)

    error_msg = str(exc.value)
    assert "Invalid metadata value types for keys" in error_msg
    assert all(key in error_msg for key in ["nested_dict", "nested_list", "nested_tuple"])


def test_handles_numeric_values(validator, valid_document):
    """Test validation of numeric metadata values."""
    valid_document["metadata"] = {"integer": 42, "float": 3.14, "zero": 0, "negative": -1}
    result = validator.process(valid_document)
    assert result["metadata"]["integer"] == 42
    assert result["metadata"]["float"] == 3.14
