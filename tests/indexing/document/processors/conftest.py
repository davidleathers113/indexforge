"""Common test fixtures for document processor tests."""

from unittest.mock import Mock

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
    mock_tracer = Mock(spec=DocumentTracer)
    mock_tracer.start_validation.return_value.__enter__.return_value = Mock()
    return mock_tracer


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


@pytest.fixture
def valid_document():
    """Create a valid test document."""
    return {
        "id": "doc1",
        "content": "Valid content that meets length requirement",
        "metadata": {"source": "test", "author": "tester"},
    }
