"""Unit tests for secure storage wrapper."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from src.core.models.documents import Document, DocumentMetadata, DocumentType
from src.core.security.encryption import EncryptedData, EncryptionConfig, EncryptionManager
from src.core.settings import Settings
from src.services.storage.document_storage import DocumentStorageService
from src.services.storage.secure_storage import SecureStorageWrapper


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for testing."""
    return tmp_path


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,
    )


@pytest.fixture
def encryption_config():
    """Create test encryption configuration."""
    return EncryptionConfig(
        master_key=SecretStr("test-master-key-that-is-sufficiently-long"),
        key_rotation_days=1,
        min_key_retention_days=2,
        pbkdf2_iterations=1000,  # Lower for tests
    )


@pytest.fixture
async def encryption_manager(encryption_config):
    """Create test encryption manager."""
    manager = EncryptionManager(encryption_config)
    await manager._init_storage()
    return manager


@pytest.fixture
def base_storage(settings):
    """Create base storage service."""
    return DocumentStorageService(settings=settings)


@pytest.fixture
def secure_storage(base_storage, encryption_manager, settings, temp_dir):
    """Create secure storage wrapper."""
    metadata_dir = temp_dir / "metadata"
    return SecureStorageWrapper(
        storage=base_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )


@pytest.fixture
def test_document():
    """Create test document."""
    return Document(
        metadata=DocumentMetadata(
            title="Test Document",
            doc_type=DocumentType.TEXT,
        ),
        content="Test content",
    )


@pytest.mark.asyncio
async def test_store_document(secure_storage, test_document):
    """Test secure document storage."""
    # Store document
    doc_id = await secure_storage.store_document(test_document)
    assert isinstance(doc_id, UUID)

    # Verify metadata is stored
    assert doc_id in secure_storage._metadata
    metadata = secure_storage._metadata[doc_id]
    assert metadata.version == 1
    assert isinstance(metadata.encryption_data, EncryptedData)

    # Verify metadata file is created
    metadata_path = secure_storage._get_metadata_path(doc_id)
    assert metadata_path.exists()
    with metadata_path.open("r") as f:
        stored_metadata = json.load(f)
        assert stored_metadata["version"] == 1


@pytest.mark.asyncio
async def test_metadata_persistence(
    base_storage, encryption_manager, settings, temp_dir, test_document
):
    """Test metadata persistence across storage instances."""
    metadata_dir = temp_dir / "metadata"

    # Create first storage instance and store document
    storage1 = SecureStorageWrapper(
        storage=base_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )
    doc_id = await storage1.store_document(test_document)

    # Create second storage instance
    storage2 = SecureStorageWrapper(
        storage=base_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )

    # Verify metadata is loaded
    assert doc_id in storage2._metadata
    assert storage2._metadata[doc_id].version == 1

    # Verify document can be decrypted
    retrieved = await storage2.get_document(doc_id)
    assert retrieved is not None
    assert retrieved.metadata.title == test_document.metadata.title
    assert retrieved.content == test_document.content


@pytest.mark.asyncio
async def test_metadata_atomic_writes(secure_storage, test_document, temp_dir):
    """Test atomic metadata file writes."""
    doc_id = await secure_storage.store_document(test_document)
    metadata_path = secure_storage._get_metadata_path(doc_id)
    temp_path = metadata_path.with_suffix(".tmp")

    # Verify temp file is cleaned up
    assert not temp_path.exists()
    assert metadata_path.exists()

    # Update document
    updated_document = test_document.copy()
    updated_document.content = "Updated content"
    await secure_storage.update_document(doc_id, updated_document)

    # Verify temp file is cleaned up after update
    assert not temp_path.exists()
    assert metadata_path.exists()


@pytest.mark.asyncio
async def test_metadata_cleanup(secure_storage, test_document):
    """Test metadata cleanup on document deletion."""
    doc_id = await secure_storage.store_document(test_document)
    metadata_path = secure_storage._get_metadata_path(doc_id)
    assert metadata_path.exists()

    # Delete document
    await secure_storage.delete_document(doc_id)

    # Verify metadata is cleaned up
    assert not metadata_path.exists()
    assert doc_id not in secure_storage._metadata


@pytest.mark.asyncio
async def test_key_rotation_with_persistence(
    base_storage, encryption_manager, settings, temp_dir, test_document
):
    """Test key rotation with persistent metadata."""
    metadata_dir = temp_dir / "metadata"
    storage = SecureStorageWrapper(
        storage=base_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )

    # Store documents
    doc_ids = []
    for i in range(3):
        doc = test_document.copy()
        doc.content = f"Content {i}"
        doc_id = await storage.store_document(doc)
        doc_ids.append(doc_id)

    # Store original metadata
    original_metadata = {}
    for doc_id in doc_ids:
        metadata_path = storage._get_metadata_path(doc_id)
        with metadata_path.open("r") as f:
            original_metadata[doc_id] = json.load(f)

    # Rotate keys
    await storage.rotate_keys()

    # Verify metadata is updated on disk
    for doc_id in doc_ids:
        metadata_path = storage._get_metadata_path(doc_id)
        with metadata_path.open("r") as f:
            new_metadata = json.load(f)
            assert new_metadata != original_metadata[doc_id]

        # Verify document can still be decrypted
        doc = await storage.get_document(doc_id)
        assert doc is not None
        assert doc.content == f"Content {doc_ids.index(doc_id)}"
