"""Tests for basic document structure validation."""

import pytest


def test_validates_dictionary_structure(validator):
    """Test validation of document dictionary structure."""
    with pytest.raises(ValueError) as exc:
        validator.process(["not", "a", "dict"])
    assert "Document must be a dictionary" in str(exc.value)


def test_rejects_empty_document(validator):
    """Test validation of empty document."""
    with pytest.raises(ValueError) as exc:
        validator.process({})
    assert "Document cannot be empty" in str(exc.value)


def test_requires_document_id(validator, valid_document):
    """Test validation of document ID field."""
    del valid_document["id"]
    with pytest.raises(ValueError) as exc:
        validator.process(valid_document)
    assert "Document must have 'id' or 'document_id' field" in str(exc.value)
