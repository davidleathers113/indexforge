"""Shared test fixtures for lineage tracking tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.core.tracking.models import DocumentLineage


@pytest.fixture
def mock_storage():
    """Create a mock storage backend."""
    storage = MagicMock()
    storage.get_lineage.return_value = None
    storage.save_lineage.return_value = None
    return storage


@pytest.fixture
def sample_doc():
    """Create a sample document lineage object."""
    return DocumentLineage(
        doc_id="doc-1",
        origin_id="origin-1",
        origin_source="test-source",
        origin_type="test-type",
        metadata={"test": "metadata"},
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )


@pytest.fixture
def sample_parent_doc():
    """Create a sample parent document lineage object."""
    return DocumentLineage(
        doc_id="parent-1",
        origin_id="parent-origin-1",
        origin_source="test-source",
        origin_type="test-type",
        metadata={"test": "parent-metadata"},
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
        children=["doc-1"],
        derived_documents=["doc-1"],
    )


@pytest.fixture
def sample_child_doc():
    """Create a sample child document lineage object."""
    return DocumentLineage(
        doc_id="child-1",
        origin_id="child-origin-1",
        origin_source="test-source",
        origin_type="test-type",
        metadata={"test": "child-metadata"},
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
        parents=["doc-1"],
        derived_from="doc-1",
    )
