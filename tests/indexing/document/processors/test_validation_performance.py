"""Performance benchmarks for document validation."""

import time
from typing import Any, Dict

import pytest


@pytest.fixture
def large_document(valid_document) -> Dict[str, Any]:
    """Create a large test document."""
    # Create a document with 1MB of content
    content = "x" * (1024 * 1024)  # 1MB of content
    valid_document["content"] = content
    return valid_document


@pytest.fixture
def document_with_max_metadata(valid_document) -> Dict[str, Any]:
    """Create a document with maximum allowed metadata."""
    valid_document["metadata"] = {
        f"key{i}": f"value{i}" for i in range(3)  # max_metadata_keys is 3
    }
    return valid_document


def test_validation_performance_baseline(validator, valid_document):
    """Benchmark validation of typical document."""
    start_time = time.perf_counter()
    validator.process(valid_document)
    duration = time.perf_counter() - start_time

    # Basic document should validate quickly
    assert duration < 0.01, f"Validation took {duration:.3f}s, expected < 0.01s"


def test_large_document_performance(validator, large_document):
    """Benchmark validation of large document."""
    start_time = time.perf_counter()
    validator.process(large_document)
    duration = time.perf_counter() - start_time

    # Even large documents should validate reasonably quickly
    assert duration < 0.1, f"Large document validation took {duration:.3f}s, expected < 0.1s"


def test_max_metadata_performance(validator, document_with_max_metadata):
    """Benchmark validation with maximum metadata."""
    start_time = time.perf_counter()
    validator.process(document_with_max_metadata)
    duration = time.perf_counter() - start_time

    # Metadata validation should be fast
    assert duration < 0.01, f"Metadata validation took {duration:.3f}s, expected < 0.01s"


def test_batch_validation_performance(validator, valid_document):
    """Benchmark validation of multiple documents in sequence."""
    batch_size = 100
    start_time = time.perf_counter()

    for _ in range(batch_size):
        validator.process(valid_document.copy())

    duration = time.perf_counter() - start_time
    avg_duration = duration / batch_size

    # Average validation time should be consistent
    assert avg_duration < 0.001, (
        f"Average validation took {avg_duration:.6f}s per document, " "expected < 0.001s"
    )
