"""Tests for document update operations."""

import time
from uuid import uuid4

import pytest

from src.core.models.documents import Document, DocumentStatus
from src.core.tracking.storage import DocumentStorage


class TestDocumentUpdates:
    """Test document update operations."""

    def test_update_metadata(self, storage: DocumentStorage, sample_document: Document):
        """Test updating document metadata."""
        storage.save_document(sample_document)
        original_updated_at = sample_document.metadata.updated_at

        # Wait to ensure timestamp difference
        time.sleep(0.1)

        updates = {
            "metadata": {
                "title": "Updated Title",
                "language": "fr",
                "custom_metadata": {"new_key": "new_value"},
            }
        }
        storage.update_document(sample_document.id, updates)

        # Verify updates
        updated_doc = storage.get_document(sample_document.id)
        assert updated_doc is not None
        assert updated_doc.metadata.title == "Updated Title"
        assert updated_doc.metadata.language == "fr"
        assert updated_doc.metadata.custom_metadata == {"new_key": "new_value"}
        assert updated_doc.metadata.updated_at > original_updated_at

    def test_update_status(self, storage: DocumentStorage, sample_document: Document):
        """Test updating document status."""
        storage.save_document(sample_document)

        updates = {"status": DocumentStatus.PROCESSED}
        storage.update_document(sample_document.id, updates)

        updated_doc = storage.get_document(sample_document.id)
        assert updated_doc is not None
        assert updated_doc.status == DocumentStatus.PROCESSED

    def test_update_error_message(self, storage: DocumentStorage, sample_document: Document):
        """Test updating document error message."""
        storage.save_document(sample_document)

        error_msg = "Test error message"
        storage.update_document(sample_document.id, {"error_message": error_msg})

        updated_doc = storage.get_document(sample_document.id)
        assert updated_doc is not None
        assert updated_doc.error_message == error_msg

    def test_update_multiple_fields(self, storage: DocumentStorage, sample_document: Document):
        """Test updating multiple document fields at once."""
        storage.save_document(sample_document)

        updates = {
            "metadata": {"title": "New Title"},
            "status": DocumentStatus.PROCESSED,
            "error_message": "Test error",
        }
        storage.update_document(sample_document.id, updates)

        updated_doc = storage.get_document(sample_document.id)
        assert updated_doc is not None
        assert updated_doc.metadata.title == "New Title"
        assert updated_doc.status == DocumentStatus.PROCESSED
        assert updated_doc.error_message == "Test error"

    def test_update_nonexistent_document(self, storage: DocumentStorage):
        """Test updating nonexistent document raises error."""
        with pytest.raises(KeyError):
            storage.update_document(uuid4(), {"status": DocumentStatus.PROCESSED})

    def test_update_invalid_status(self, storage: DocumentStorage, sample_document: Document):
        """Test updating to invalid status raises error."""
        storage.save_document(sample_document)

        with pytest.raises(ValueError):
            storage.update_document(sample_document.id, {"status": "invalid_status"})  # type: ignore

    def test_update_timestamp(self, storage: DocumentStorage, sample_document: Document):
        """Test metadata timestamp is updated."""
        storage.save_document(sample_document)
        original_time = sample_document.metadata.updated_at

        time.sleep(0.1)  # Ensure time difference
        storage.update_document(sample_document.id, {"metadata": {"title": "New Title"}})

        updated_doc = storage.get_document(sample_document.id)
        assert updated_doc is not None
        assert updated_doc.metadata.updated_at > original_time
