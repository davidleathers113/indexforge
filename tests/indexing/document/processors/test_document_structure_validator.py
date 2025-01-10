"""Unit tests for document structure validator.

This module contains tests for the DocumentStructureValidator class,
covering validation logic, metrics collection, and tracing integration.
"""

from unittest.mock import Mock, patch

import pytest

from src.api.monitoring.collectors.document_metrics import DocumentMetrics
from src.api.monitoring.tracing import DocumentTracer
from src.indexing.document.processors.document_structure_validator import DocumentStructureValidator


@pytest.fixture
def metrics():
    """Create mock metrics collector."""
    return Mock(spec=DocumentMetrics)


@pytest.fixture
def tracer():
    """Create mock tracer."""
    return Mock(spec=DocumentTracer)


@pytest.fixture
def validator(metrics, tracer):
    """Create document validator instance."""
    return DocumentStructureValidator(
        metrics=metrics,
        tracer=tracer,
        required_fields={"content", "metadata"},
        content_min_length=10,
        max_metadata_keys=3,
    )


def test_valid_document_processing(validator, metrics, tracer):
    """Test processing of valid document."""
    # Setup
    document = {
        "id": "doc1",
        "content": "Valid content that meets length requirement",
        "metadata": {"source": "test", "author": "tester"},
    }

    mock_span = Mock()
    tracer.start_validation.return_value.__enter__.return_value = mock_span

    # Execute
    result = validator.process(document)

    # Verify
    assert result == document
    metrics.record_validation_check.assert_any_call("structure", "pass")
    metrics.record_validation_check.assert_any_call("required_fields", "pass")
    metrics.record_validation_check.assert_any_call("content", "pass")
    metrics.record_validation_check.assert_any_call("metadata", "pass")

    mock_span.set_attribute.assert_any_call("validation.structure", "complete")
    mock_span.set_attribute.assert_any_call("validation.required_fields", "complete")
    mock_span.set_attribute.assert_any_call("validation.content", "complete")
    mock_span.set_attribute.assert_any_call("validation.metadata", "complete")


def test_missing_required_fields(validator):
    """Test validation of document with missing required fields."""
    document = {
        "id": "doc1",
        "content": "Valid content",
        # Missing metadata
    }

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Missing required fields: metadata" in str(exc.value)


def test_invalid_content_type(validator):
    """Test validation of document with non-string content."""
    document = {"id": "doc1", "content": {"invalid": "type"}, "metadata": {}}

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Content must be a string" in str(exc.value)


def test_content_too_short(validator):
    """Test validation of document with content below minimum length."""
    document = {"id": "doc1", "content": "short", "metadata": {}}

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Content length" in str(exc.value)
    assert "below minimum required" in str(exc.value)


def test_invalid_metadata_type(validator):
    """Test validation of document with non-dict metadata."""
    document = {
        "id": "doc1",
        "content": "Valid content that meets length requirement",
        "metadata": "invalid",
    }

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Metadata must be a dictionary" in str(exc.value)


def test_too_many_metadata_keys(validator):
    """Test validation of document with too many metadata keys."""
    document = {
        "id": "doc1",
        "content": "Valid content that meets length requirement",
        "metadata": {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",  # Exceeds max_metadata_keys=3
        },
    }

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Number of metadata keys" in str(exc.value)
    assert "exceeds maximum allowed" in str(exc.value)


def test_invalid_metadata_value_types(validator):
    """Test validation of document with invalid metadata value types."""
    document = {
        "id": "doc1",
        "content": "Valid content that meets length requirement",
        "metadata": {
            "valid1": "string",
            "valid2": 123,
            "invalid1": ["list"],
            "invalid2": {"nested": "dict"},
        },
    }

    with pytest.raises(ValueError) as exc:
        validator.process(document)

    assert "Invalid metadata value types for keys" in str(exc.value)
    assert "invalid1" in str(exc.value)
    assert "invalid2" in str(exc.value)


def test_metrics_recording_on_error(validator, metrics):
    """Test metrics recording when validation fails."""
    document = {"id": "doc1", "content": "short", "metadata": {}}

    with pytest.raises(ValueError):
        validator.process(document)

    metrics.record_error.assert_called_once()
    assert metrics.record_error.call_args[1]["error_type"] == "ValueError"
    assert metrics.record_error.call_args[1]["stage"] == "document_validator"
