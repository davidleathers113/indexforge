"""Test fixtures for integration testing."""

from datetime import UTC, datetime

import pytest

from src.core.models.lineage import DocumentLineage


class MockStorage:
    """Mock storage backend for testing."""

    def __init__(self):
        """Initialize mock storage."""
        self._lineage: dict[str, DocumentLineage] = {}
        self._last_modified = datetime.now(UTC)

    def get_lineage(self, doc_id: str) -> DocumentLineage | None:
        """Get document lineage."""
        return self._lineage.get(doc_id)

    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save document lineage."""
        self._lineage[lineage.doc_id] = lineage
        self._last_modified = datetime.now(UTC)

    def get_all_lineage(self) -> dict[str, DocumentLineage]:
        """Get all document lineage data."""
        return self._lineage.copy()

    def delete_lineage(self, doc_id: str) -> None:
        """Delete document lineage."""
        if doc_id in self._lineage:
            del self._lineage[doc_id]
            self._last_modified = datetime.now(UTC)

    def get_last_modified(self) -> datetime:
        """Get last modification time."""
        return self._last_modified


@pytest.fixture
def mock_storage():
    """Create a mock storage instance for testing."""
    return MockStorage()
