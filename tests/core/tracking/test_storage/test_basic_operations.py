"""Tests for basic document storage operations."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType
from src.core.models.settings import Settings
from src.core.tracking.storage import DocumentStorage

from .conftest import create_test_document


class TestBasicOperations:
    """Test basic CRUD operations for document storage."""

    def test_storage_initialization(self, storage_path: Path, settings: Settings):
        """Test storage initialization creates directory."""
        storage = DocumentStorage(storage_path, settings)
        assert storage_path.exists()
        assert storage_path.is_dir()
        assert len(storage.documents) == 0
        assert storage.metrics is not None

    def test_save_and_get_document(self, storage: DocumentStorage, sample_document: Document):
        """Test saving and retrieving a document."""
        storage.save_document(sample_document)
        retrieved = storage.get_document(sample_document.id)
        assert retrieved is not None
        assert retrieved.id == sample_document.id
        assert retrieved.metadata.title == sample_document.metadata.title
        assert retrieved.metadata.doc_type == sample_document.metadata.doc_type
        assert retrieved.status == sample_document.status

    def test_delete_document(self, storage: DocumentStorage, sample_document: Document):
        """Test deleting a document."""
        storage.save_document(sample_document)
        storage.delete_document(sample_document.id)
        assert storage.get_document(sample_document.id) is None

    def test_delete_nonexistent_document(self, storage: DocumentStorage):
        """Test deleting a nonexistent document raises KeyError."""
        with pytest.raises(KeyError):
            storage.delete_document(uuid4())

    def test_save_invalid_document_type(self, storage: DocumentStorage, sample_document: Document):
        """Test saving a document with invalid type raises ValueError."""
        sample_document.metadata.doc_type = "invalid_type"  # type: ignore
        with pytest.raises(ValueError):
            storage.save_document(sample_document)

    def test_document_persistence(
        self, storage_path: Path, settings: Settings, sample_document: Document
    ):
        """Test document persistence across storage instances."""
        # Save document
        storage1 = DocumentStorage(storage_path, settings)
        storage1.save_document(sample_document)

        # Load in new instance
        storage2 = DocumentStorage(storage_path, settings)
        retrieved = storage2.get_document(sample_document.id)
        assert retrieved is not None
        assert retrieved.id == sample_document.id
        assert retrieved.metadata.title == sample_document.metadata.title
