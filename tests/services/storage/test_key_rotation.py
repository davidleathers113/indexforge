"""Tests for key rotation handler.

This module contains tests for the KeyRotationHandler class, ensuring proper
re-encryption of documents during key rotation.
"""

import logging
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.core.security.encryption import EncryptionManager
from src.core.settings import Settings
from src.services.storage.key_rotation import KeyRotationHandler
from src.services.storage.secure_storage import SecureStorageWrapper

from .test_secure_storage import TestDocument, mock_storage

logger = logging.getLogger(__name__)


@pytest.fixture
def test_documents() -> list[TestDocument]:
    """Create a list of test documents.

    Returns:
        List of test documents
    """
    return [
        TestDocument(id=uuid4(), content=f"test content {i}", metadata={"test": f"value {i}"})
        for i in range(3)
    ]


@pytest.fixture
def encryption_manager() -> EncryptionManager:
    """Create an encryption manager.

    Returns:
        Encryption manager instance
    """
    return EncryptionManager()


@pytest.fixture
def settings() -> Settings:
    """Create settings instance.

    Returns:
        Settings instance
    """
    return Settings()


@pytest.fixture
def metadata_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for metadata.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path to temporary metadata directory
    """
    metadata_path = tmp_path / "metadata"
    metadata_path.mkdir()
    return metadata_path


@pytest.fixture
async def secure_storage_with_docs(
    mock_storage,
    encryption_manager: EncryptionManager,
    settings: Settings,
    metadata_dir: Path,
    test_documents: list[TestDocument],
) -> tuple[SecureStorageWrapper[TestDocument], list[UUID]]:
    """Create a secure storage wrapper with pre-stored documents.

    Args:
        mock_storage: Mock storage implementation
        encryption_manager: Encryption manager
        settings: Settings instance
        metadata_dir: Temporary metadata directory
        test_documents: List of test documents

    Returns:
        Tuple of (secure storage wrapper, list of document IDs)
    """
    storage = SecureStorageWrapper(
        storage=mock_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )

    doc_ids = []
    for doc in test_documents:
        doc_id = await storage.store_document(doc)
        doc_ids.append(doc_id)

    return storage, doc_ids


@pytest.fixture
def key_rotation_handler(
    secure_storage_with_docs: tuple[SecureStorageWrapper[TestDocument], list[UUID]],
    encryption_manager: EncryptionManager,
) -> KeyRotationHandler[TestDocument]:
    """Create a key rotation handler instance.

    Args:
        secure_storage_with_docs: Tuple of (secure storage wrapper, document IDs)
        encryption_manager: Encryption manager

    Returns:
        Key rotation handler instance
    """
    storage, _ = secure_storage_with_docs
    return KeyRotationHandler(storage=storage, encryption=encryption_manager)


@pytest.mark.asyncio
async def test_rotate_keys_success(
    key_rotation_handler: KeyRotationHandler[TestDocument],
    secure_storage_with_docs: tuple[SecureStorageWrapper[TestDocument], list[UUID]],
    test_documents: list[TestDocument],
):
    """Test successful key rotation for all documents.

    Args:
        key_rotation_handler: Key rotation handler
        secure_storage_with_docs: Tuple of (secure storage wrapper, document IDs)
        test_documents: List of test documents
    """
    storage, doc_ids = secure_storage_with_docs

    # Rotate keys
    successful, failed = await key_rotation_handler.rotate_keys(doc_ids)

    # Verify all documents were re-encrypted
    assert len(successful) == len(doc_ids)
    assert not failed

    # Verify documents can still be retrieved
    for i, doc_id in enumerate(doc_ids):
        retrieved = await storage.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.content == test_documents[i].content
        assert retrieved.metadata == test_documents[i].metadata


@pytest.mark.asyncio
async def test_rotate_keys_partial_failure(
    key_rotation_handler: KeyRotationHandler[TestDocument],
    secure_storage_with_docs: tuple[SecureStorageWrapper[TestDocument], list[UUID]],
):
    """Test key rotation with some nonexistent documents.

    Args:
        key_rotation_handler: Key rotation handler
        secure_storage_with_docs: Tuple of (secure storage wrapper, document IDs)
    """
    _, doc_ids = secure_storage_with_docs
    nonexistent_id = uuid4()
    all_ids = doc_ids + [nonexistent_id]

    # Rotate keys
    successful, failed = await key_rotation_handler.rotate_keys(all_ids)

    # Verify results
    assert len(successful) == len(doc_ids)
    assert len(failed) == 1
    assert failed[0] == nonexistent_id


@pytest.mark.asyncio
async def test_rotate_keys_empty_list(key_rotation_handler: KeyRotationHandler[TestDocument]):
    """Test key rotation with empty document list.

    Args:
        key_rotation_handler: Key rotation handler
    """
    successful, failed = await key_rotation_handler.rotate_keys([])
    assert not successful
    assert not failed


@pytest.mark.asyncio
async def test_rotate_keys_storage_error(
    key_rotation_handler: KeyRotationHandler[TestDocument],
    secure_storage_with_docs: tuple[SecureStorageWrapper[TestDocument], list[UUID]],
    monkeypatch,
):
    """Test key rotation with storage errors.

    Args:
        key_rotation_handler: Key rotation handler
        secure_storage_with_docs: Tuple of (secure storage wrapper, document IDs)
        monkeypatch: Pytest monkeypatch fixture
    """
    storage, doc_ids = secure_storage_with_docs

    # Mock storage error
    async def mock_store(*args, **kwargs):
        raise Exception("Storage error")

    monkeypatch.setattr(storage, "store_document", mock_store)

    # Rotate keys
    successful, failed = await key_rotation_handler.rotate_keys(doc_ids)

    # Verify all documents failed
    assert not successful
    assert len(failed) == len(doc_ids)
    assert all(doc_id in failed for doc_id in doc_ids)
