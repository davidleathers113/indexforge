"""Tests for document content validation."""

import pytest


def test_requires_string_content(validator, valid_document):
    """Test validation of content type."""
    valid_document["content"] = {"not": "a string"}
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Content must be a string" in str(exc.value)


def test_enforces_minimum_content_length(validator, valid_document):
    """Test validation of content length."""
    valid_document["content"] = "too short"
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Content length" in str(exc.value)
    assert "below minimum required" in str(exc.value)


def test_accepts_valid_content(validator, valid_document):
    """Test acceptance of valid content."""
    result = validator.process(valid_document)
    assert result["content"] == valid_document["content"]
