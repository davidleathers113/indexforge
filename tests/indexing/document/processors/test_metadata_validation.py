"""Tests for document metadata validation."""

import pytest


def test_requires_dictionary_metadata(validator, valid_document):
    """Test validation of metadata type."""
    valid_document["metadata"] = "not a dict"
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Metadata must be a dictionary" in str(exc.value)


def test_enforces_max_metadata_keys(validator, valid_document):
    """Test validation of metadata key count."""
    valid_document["metadata"] = {f"key{i}": f"value{i}" for i in range(4)}  # Exceeds max of 3
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Number of metadata keys" in str(exc.value)
    assert "exceeds maximum allowed" in str(exc.value)


def test_validates_metadata_value_types(validator, valid_document):
    """Test validation of metadata value types."""
    valid_document["metadata"] = {"valid": "string", "invalid": ["list"]}
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Invalid metadata value types for keys" in str(exc.value)
    assert "invalid" in str(exc.value)
