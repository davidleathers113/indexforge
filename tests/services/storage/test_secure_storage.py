"""Tests for secure storage wrapper.

This module contains tests for the SecureStorageWrapper class, ensuring proper
encryption, decryption, and storage of documents.
"""

import logging
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from src.core.interfaces.storage import DocumentStorage
from src.core.models.documents import Document
from src.core.security.encryption import EncryptionManager
from src.core.settings import Settings
from src.services.storage.secure_storage import SecureStorageWrapper

logger = logging.getLogger(__name__)


class TestDocument(Document):
    """Test document model."""

    content: str
    metadata: dict = {}


@pytest.fixture
def test_document() -> TestDocument:
    """Create a test document.

    Returns:
        Sample test document
    """
    return TestDocument(id=uuid4(), content="test content", metadata={"test": "value"})


@pytest.fixture
def mock_storage() -> DocumentStorage[TestDocument]:
    """Create a mock storage implementation.

    Returns:
        Mock document storage
    """

    class MockStorage(DocumentStorage[TestDocument]):
        def __init__(self):
            self.documents = {}

        async def store_document(self, document: TestDocument) -> UUID:
            self.documents[document.id] = document
            return document.id

        async def get_document(self, document_id: UUID) -> TestDocument | None:
            return self.documents.get(document_id)

        async def delete_document(self, document_id: UUID) -> None:
            self.documents.pop(document_id, None)

    return MockStorage()


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
def secure_storage(
    mock_storage: DocumentStorage[TestDocument],
    encryption_manager: EncryptionManager,
    settings: Settings,
    metadata_dir: Path,
) -> SecureStorageWrapper[TestDocument]:
    """Create a secure storage wrapper instance.

    Args:
        mock_storage: Mock storage implementation
        encryption_manager: Encryption manager
        settings: Settings instance
        metadata_dir: Temporary metadata directory

    Returns:
        Secure storage wrapper instance
    """
    return SecureStorageWrapper(
        storage=mock_storage,
        encryption_manager=encryption_manager,
        settings=settings,
        metadata_dir=metadata_dir,
    )


@pytest.mark.asyncio
async def test_store_and_get_document(
    secure_storage: SecureStorageWrapper[TestDocument], test_document: TestDocument
):
    """Test storing and retrieving a document.

    Args:
        secure_storage: Secure storage wrapper
        test_document: Test document
    """
    # Store document
    doc_id = await secure_storage.store_document(test_document)
    assert doc_id == test_document.id

    # Retrieve and verify
    retrieved = await secure_storage.get_document(doc_id)
    assert retrieved is not None
    assert retrieved.id == test_document.id
    assert retrieved.content == test_document.content
    assert retrieved.metadata == test_document.metadata


@pytest.mark.asyncio
async def test_delete_document(
    secure_storage: SecureStorageWrapper[TestDocument], test_document: TestDocument
):
    """Test deleting a document.

    Args:
        secure_storage: Secure storage wrapper
        test_document: Test document
    """
    # Store document
    doc_id = await secure_storage.store_document(test_document)

    # Delete and verify
    await secure_storage.delete_document(doc_id)
    retrieved = await secure_storage.get_document(doc_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_store_invalid_document(secure_storage: SecureStorageWrapper[TestDocument]):
    """Test handling invalid document storage.

    Args:
        secure_storage: Secure storage wrapper
    """
    with pytest.raises(ValueError):
        await secure_storage.store_document(None)  # type: ignore


@pytest.mark.asyncio
async def test_get_nonexistent_document(secure_storage: SecureStorageWrapper[TestDocument]):
    """Test retrieving nonexistent document.

    Args:
        secure_storage: Secure storage wrapper
    """
    doc_id = uuid4()
    retrieved = await secure_storage.get_document(doc_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent_document(secure_storage: SecureStorageWrapper[TestDocument]):
    """Test deleting nonexistent document.

    Args:
        secure_storage: Secure storage wrapper
    """
    doc_id = uuid4()
    # Should not raise an error
    await secure_storage.delete_document(doc_id)


@pytest.mark.asyncio
async def test_encryption_decryption(
    secure_storage: SecureStorageWrapper[TestDocument],
    test_document: TestDocument,
    mock_storage: DocumentStorage[TestDocument],
):
    """Test document encryption and decryption.

    Args:
        secure_storage: Secure storage wrapper
        test_document: Test document
        mock_storage: Mock storage implementation
    """
    # Store document
    doc_id = await secure_storage.store_document(test_document)

    # Verify stored document is encrypted
    stored = mock_storage.documents[doc_id]
    assert stored.content != test_document.content

    # Verify retrieval decrypts correctly
    retrieved = await secure_storage.get_document(doc_id)
    assert retrieved is not None
    assert retrieved.content == test_document.content
