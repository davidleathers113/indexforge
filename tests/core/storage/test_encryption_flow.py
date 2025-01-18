"""End-to-end encryption flow tests.

This module contains integration tests that verify the complete encryption flow,
including document encryption, storage, key rotation, and metadata management.
Tests focus on:
- End-to-end document encryption
- Metadata persistence
- Key rotation with re-encryption
- Error handling during encryption operations
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from src.core.models.documents import Document
from src.core.storage.secure.key_rotation import KeyRotationHandler
from src.core.storage.secure.metadata import MetadataHandler
from src.core.storage.secure.storage import SecureStorageWrapper
from src.core.storage.strategies.memory_storage import MemoryStorage


class TestDocument(BaseModel):
    """Test document model."""

    id: UUID
    content: str
    created_at: datetime = datetime.now(UTC)
    metadata: dict = {}


@pytest.fixture
def metadata_dir(tmp_path) -> Path:
    """Create a temporary directory for metadata."""
    return tmp_path / "metadata"


@pytest.fixture
async def metadata_handler(metadata_dir) -> MetadataHandler:
    """Create a metadata handler for testing."""
    handler = MetadataHandler(metadata_dir=metadata_dir)
    yield handler
    await handler.clear()


@pytest.fixture
async def secure_storage(metadata_handler) -> AsyncGenerator[SecureStorageWrapper, None]:
    """Create a secure storage wrapper with memory storage."""
    storage = MemoryStorage()
    wrapper = SecureStorageWrapper(storage=storage, metadata_handler=metadata_handler)
    yield wrapper
    await storage.clear()


@pytest.fixture
async def key_rotation_handler(secure_storage) -> KeyRotationHandler:
    """Create a key rotation handler for testing."""
    return KeyRotationHandler(storage=secure_storage)


async def test_end_to_end_encryption(secure_storage, metadata_handler):
    """Test end-to-end document encryption flow."""
    # Create and store an encrypted document
    doc_id = uuid4()
    doc = TestDocument(id=doc_id, content="Test document")
    await secure_storage.store_document(doc)

    # Verify metadata was created
    metadata = await metadata_handler.get_metadata(doc_id)
    assert metadata is not None
    assert metadata.doc_id == doc_id
    assert metadata.encryption_key is not None

    # Retrieve and verify decrypted document
    stored_doc = await secure_storage.get_document(doc_id)
    assert stored_doc == doc

    # Delete document and verify cleanup
    await secure_storage.delete_document(doc_id)
    assert await secure_storage.get_document(doc_id) is None
    assert await metadata_handler.get_metadata(doc_id) is None


async def test_key_rotation_flow(secure_storage, key_rotation_handler):
    """Test key rotation with document re-encryption."""
    # Store multiple documents
    num_docs = 5
    docs = [TestDocument(id=uuid4(), content=f"Test document {i}") for i in range(num_docs)]
    doc_ids = []

    for doc in docs:
        await secure_storage.store_document(doc)
        doc_ids.append(doc.id)

    # Perform key rotation
    success_ids, failure_ids = await key_rotation_handler.rotate_keys(doc_ids)
    assert len(success_ids) == num_docs
    assert len(failure_ids) == 0

    # Verify documents are still accessible
    for doc in docs:
        stored_doc = await secure_storage.get_document(doc.id)
        assert stored_doc == doc


async def test_concurrent_encryption(secure_storage):
    """Test concurrent encryption operations."""
    num_docs = 20
    docs = [TestDocument(id=uuid4(), content=f"Test document {i}") for i in range(num_docs)]

    # Concurrent encrypted saves
    await asyncio.gather(*[secure_storage.store_document(doc) for doc in docs])

    # Concurrent decrypted gets
    stored_docs = await asyncio.gather(*[secure_storage.get_document(doc.id) for doc in docs])
    assert all(a == b for a, b in zip(stored_docs, docs))


async def test_encryption_error_handling(secure_storage, metadata_handler):
    """Test error handling during encryption operations."""
    doc_id = uuid4()
    doc = TestDocument(id=doc_id, content="Test document")

    # Test invalid document
    with pytest.raises(ValueError):
        await secure_storage.store_document(None)

    # Test missing document
    assert await secure_storage.get_document(uuid4()) is None

    # Test metadata corruption
    await secure_storage.store_document(doc)
    await metadata_handler.delete_metadata(doc_id)

    # Should raise when metadata is missing
    with pytest.raises(ValueError):
        await secure_storage.get_document(doc_id)
