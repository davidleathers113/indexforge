"""Tests for storage metrics collection."""

from uuid import uuid4

import pytest

from src.core.models.documents import Document, DocumentStatus
from src.core.models.settings import Settings
from src.core.tracking.storage import DocumentStorage


class TestStorageMetrics:
    """Test storage metrics collection."""

    def test_metrics_enabled(self, storage: DocumentStorage, sample_document: Document):
        """Test metrics collection when enabled."""
        storage.save_document(sample_document)
        retrieved = storage.get_document(sample_document.id)
        assert retrieved is not None

        metrics = storage.metrics.get_metrics()
        assert "save_document" in metrics
        assert "get_document" in metrics
        assert len(metrics["save_document"]) == 1
        assert len(metrics["get_document"]) == 1

    def test_metrics_disabled(self, storage_path: Path):
        """Test storage works correctly with metrics disabled."""
        settings = Settings(storage_path=storage_path, metrics_enabled=False)
        storage = DocumentStorage(storage_path, settings)
        assert storage.metrics is None

        # Operations should work without metrics
        doc = storage.get_document(uuid4())
        assert doc is None

    def test_operation_timing(self, storage: DocumentStorage, sample_document: Document):
        """Test operation timing is recorded."""
        storage.save_document(sample_document)
        metrics = storage.metrics.get_metrics()

        assert "save_document" in metrics
        assert len(metrics["save_document"]) == 1
        assert metrics["save_document"][0] > 0  # Time should be positive

    def test_failed_operation_metrics(self, storage: DocumentStorage):
        """Test metrics are recorded for failed operations."""
        with pytest.raises(KeyError):
            storage.delete_document(uuid4())

        metrics = storage.metrics.get_metrics()
        assert "delete_document" in metrics
        assert len(metrics["delete_document"]) == 1

    def test_update_operation_metrics(self, storage: DocumentStorage, sample_document: Document):
        """Test metrics for update operations."""
        storage.save_document(sample_document)
        storage.update_document(sample_document.id, {"status": DocumentStatus.PROCESSED})

        metrics = storage.metrics.get_metrics()
        assert "update_document" in metrics
        assert len(metrics["update_document"]) == 1

    def test_metrics_persistence(self, storage: DocumentStorage, sample_document: Document):
        """Test metrics collection across operations."""
        # Perform multiple operations
        storage.save_document(sample_document)
        storage.get_document(sample_document.id)
        storage.update_document(sample_document.id, {"status": DocumentStatus.PROCESSED})
        storage.delete_document(sample_document.id)

        # Verify metrics
        metrics = storage.metrics.get_metrics()
        assert "save_document" in metrics
        assert "get_document" in metrics
        assert "update_document" in metrics
        assert "delete_document" in metrics
        assert len(metrics["save_document"]) == 1
        assert len(metrics["get_document"]) == 1
        assert len(metrics["update_document"]) == 1
        assert len(metrics["delete_document"]) == 1
