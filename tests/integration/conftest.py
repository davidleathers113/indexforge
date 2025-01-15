from datetime import datetime, timezone
import tracemalloc
from typing import Any, Dict

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import SourceTracker
from src.indexing.schema import SchemaDefinition


@pytest.fixture
def base_schema():
    """Fixture providing the base schema configuration."""
    return SchemaDefinition.get_schema(class_name="Document")


@pytest.fixture
def doc_tracker():
    """Fixture providing a configured SourceTracker instance."""
    return SourceTracker("word")


@pytest.fixture
def valid_document() -> Dict[str, Any]:
    """Fixture providing a valid document that meets all schema requirements."""
    return {
        "content_body": "Test document content",
        "content_summary": "Test summary",
        "content_title": "Test Document",
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "parent_id": None,
        "chunk_ids": [],
        "embedding": [0.1] * 384,  # 384-dimensional vector
    }


@pytest.fixture
def mock_processor(mocker):
    """Fixture providing a mocked document processor."""
    processor = mocker.Mock()
    processor.process.return_value = {
        "content": {
            "full_text": "Test document content",
            "summary": "Test summary",
            "title": "Test Document",
        },
        "metadata": {"source_type": "word", "created_at": datetime.now(timezone.utc).isoformat()},
    }
    return processor


def pytest_configure(config):
    """Configure pytest with enhanced exception handling."""
    tracemalloc.start()


def pytest_unconfigure(config):
    """Cleanup pytest configuration."""
    tracemalloc.stop()
