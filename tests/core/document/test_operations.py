"""Tests for document operations."""

from datetime import datetime
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.core.document.operations import (
    DocumentNotFoundError,
    DocumentOperations,
    DocumentOperationsService,
    ServiceStateError,
)
from src.core.models import Document, DocumentStatus, DocumentType
from src.core.types.service import ServiceState


@pytest.fixture
def storage(mocker: MockerFixture):
    """Mock storage strategy."""
    storage = mocker.Mock()
    storage.health_check = mocker.AsyncMock(return_value=True)
    return storage


@pytest.fixture
async def service(storage):
    """Document operations service instance."""
    async with DocumentOperationsService(storage) as service:
        yield service


@pytest.mark.asyncio
async def test_service_lifecycle(storage):
    """Test service initialization and cleanup."""
    service = DocumentOperationsService(storage)
    assert service.state == ServiceState.CREATED

    await service.initialize()
    assert service.state == ServiceState.RUNNING
    storage.health_check.assert_called_once()

    await service.cleanup()
    assert service.state == ServiceState.STOPPED


@pytest.mark.asyncio
async def test_service_initialization_failure(storage):
    """Test service initialization failure."""
    storage.health_check.side_effect = Exception("Storage error")
    service = DocumentOperationsService(storage)

    with pytest.raises(ServiceStateError) as exc:
        await service.initialize()
    assert "Failed to initialize storage" in str(exc.value)
    assert service.state == ServiceState.ERROR


@pytest.mark.asyncio
async def test_create_document(service, storage):
    """Test document creation."""
    content = "Test content"
    metadata = DocumentMetadata(author="test.user")

    doc = await service.create_document(content=content, metadata=metadata)

    assert doc.content == content
    assert doc.metadata.author == "test.user"
    storage.save.assert_called_once_with(str(doc.id), doc.dict())


@pytest.mark.asyncio
async def test_get_document(service, storage):
    """Test retrieving a document."""
    doc_id = uuid4()
    doc_data = {
        "id": str(doc_id),
        "content": "Test content",
        "metadata": {"author": "test.user"},
        "relationships": [],
        "is_active": True,
    }
    storage.load.return_value = doc_data

    doc = await service.get_document(doc_id)

    assert doc.id == doc_id
    assert doc.content == "Test content"
    assert doc.metadata.author == "test.user"
    storage.load.assert_called_once_with(str(doc_id))


@pytest.mark.asyncio
async def test_get_document_not_found(service, storage):
    """Test error when document not found."""
    doc_id = uuid4()
    storage.load.return_value = None

    with pytest.raises(DocumentNotFoundError):
        await service.get_document(doc_id)


@pytest.mark.asyncio
async def test_update_document(service, storage):
    """Test document update."""
    doc_id = uuid4()
    original_doc = Document(
        id=doc_id,
        content="Original content",
        metadata=DocumentMetadata(author="test.user"),
    )
    storage.load.return_value = original_doc.dict()

    updated_doc = await service.update_document(
        doc_id=doc_id,
        content="Updated content",
        metadata={"author": "new.user"},
    )

    assert updated_doc.content == "Updated content"
    assert updated_doc.metadata.author == "new.user"
    assert updated_doc.metadata.updated_at > original_doc.metadata.updated_at
    storage.save.assert_called_once()


@pytest.mark.asyncio
async def test_delete_document(service, storage):
    """Test document deletion (soft delete)."""
    doc_id = uuid4()
    original_doc = Document(
        id=doc_id,
        content="Test content",
        metadata=DocumentMetadata(author="test.user"),
    )
    storage.load.return_value = original_doc.dict()

    await service.delete_document(doc_id)

    save_call = storage.save.call_args[0]
    saved_doc = Document.parse_obj(save_call[1])
    assert saved_doc.is_active is False


@pytest.mark.asyncio
async def test_list_documents(service, storage):
    """Test listing documents."""
    docs = [
        Document(
            id=uuid4(),
            content=f"Content {i}",
            metadata=DocumentMetadata(
                author="test.user",
                created_at=datetime.utcnow(),
            ),
        ).dict()
        for i in range(3)
    ]

    storage.iterate.return_value = aiter([(str(i), doc) for i, doc in enumerate(docs)])

    result = await service.list_documents()

    assert len(result) == 3
    assert all(isinstance(doc, Document) for doc in result)


@pytest.mark.asyncio
async def test_list_documents_with_parent(service, storage):
    """Test listing documents with parent filter."""
    parent_id = uuid4()
    docs = [
        Document(
            id=uuid4(),
            content=f"Content {i}",
            parent_id=parent_id if i < 2 else None,
            metadata=DocumentMetadata(author="test.user"),
        ).dict()
        for i in range(3)
    ]

    storage.iterate.return_value = aiter([(str(i), doc) for i, doc in enumerate(docs)])

    result = await service.list_documents(parent_id=parent_id)

    assert len(result) == 2
    assert all(doc.parent_id == parent_id for doc in result)


@pytest.mark.asyncio
async def test_service_health_check(service, storage):
    """Test service health check."""
    storage.health_check.return_value = True
    assert await service.health_check() is True

    storage.health_check.side_effect = Exception("Storage error")
    assert await service.health_check() is False
