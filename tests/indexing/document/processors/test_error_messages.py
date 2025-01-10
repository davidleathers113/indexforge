"""Tests for validation error message consistency."""

import pytest


def test_empty_document_error_message(validator):
    """Test exact error message for empty document."""
    with pytest.raises(ValueError, match=r"^Document cannot be empty$"):
        validator.process({})


def test_missing_id_error_message(validator, valid_document):
    """Test exact error message for missing document ID."""
    del valid_document["id"]
    with pytest.raises(ValueError, match=r"^Document must have 'id' or 'document_id' field$"):
        validator.process(valid_document)


def test_invalid_content_type_message(validator, valid_document):
    """Test exact error message for invalid content type."""
    valid_document["content"] = {"invalid": "type"}
    with pytest.raises(ValueError, match=r"^Content must be a string$"):
        validator.process(valid_document)


def test_content_length_error_message(validator, valid_document):
    """Test exact error message for content length validation."""
    valid_document["content"] = "short"
    with pytest.raises(
        ValueError, match=r"^Content length \(\d+\) below minimum required \(\d+\)$"
    ):
        validator.process(valid_document)


def test_metadata_type_error_message(validator, valid_document):
    """Test exact error message for invalid metadata type."""
    valid_document["metadata"] = "not a dict"
    with pytest.raises(ValueError, match=r"^Metadata must be a dictionary$"):
        validator.process(valid_document)


def test_metadata_keys_error_message(validator, valid_document):
    """Test exact error message for too many metadata keys."""
    valid_document["metadata"] = {f"key{i}": str(i) for i in range(4)}
    with pytest.raises(
        ValueError, match=r"^Number of metadata keys \(\d+\) exceeds maximum allowed \(\d+\)$"
    ):
        validator.process(valid_document)
