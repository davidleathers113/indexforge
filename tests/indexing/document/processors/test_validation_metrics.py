"""Tests for validation metrics and tracing.

This module verifies that the document validator correctly records metrics
and traces for both successful and failed validation scenarios.
"""

from unittest.mock import Mock


def test_records_successful_validation_metrics(validator, metrics, valid_document):
    """Test recording of successful validation metrics.

    Verifies that all validation checks are recorded as 'pass' when
    processing a valid document. Each validation stage (structure,
    required fields, content, metadata) should be recorded separately.
    """
    validator.process(valid_document)

    metrics.record_validation_check.assert_any_call("structure", "pass")
    metrics.record_validation_check.assert_any_call("required_fields", "pass")
    metrics.record_validation_check.assert_any_call("content", "pass")
    metrics.record_validation_check.assert_any_call("metadata", "pass")


def test_records_validation_error_metrics(validator, metrics, valid_document):
    """Test recording of validation error metrics.

    Verifies that validation errors are properly recorded with the correct
    error type and processing stage. This test intentionally triggers a
    ValueError by providing invalid content.
    """
    valid_document["content"] = ["invalid"]

    try:
        validator.process(valid_document)
    except ValueError:
        pass

    metrics.record_error.assert_called_once()
    assert metrics.record_error.call_args[1]["error_type"] == "ValueError"
    assert metrics.record_error.call_args[1]["stage"] == "document_validator"


def test_records_validation_spans(validator, tracer, valid_document):
    """Test recording of validation spans.

    Verifies that OpenTelemetry spans are created and populated with
    appropriate attributes for each validation stage. The mock span
    should receive attributes indicating completion of each stage.
    """
    mock_span = Mock()
    tracer.start_validation.return_value.__enter__.return_value = mock_span

    validator.process(valid_document)

    mock_span.set_attribute.assert_any_call("validation.structure", "complete")
    mock_span.set_attribute.assert_any_call("validation.required_fields", "complete")
    mock_span.set_attribute.assert_any_call("validation.content", "complete")
    mock_span.set_attribute.assert_any_call("validation.metadata", "complete")
