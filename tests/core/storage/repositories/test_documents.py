"""Tests for document repository implementation."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models.documents import Document, DocumentMetadata, DocumentStatus
from src.core.storage.repositories.base import DocumentExistsError, DocumentNotFoundError
from src.core.storage.repositories.documents import DocumentRepository


@pytest.fixture
def test_doc() -> Document:
    """Create a test document."""
    doc_id = uuid4()
    return Document(
        id=doc_id,
        content="test content",
        metadata=DocumentMetadata(
            title="Test Doc",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            source="test",
        ),
        status=DocumentStatus.PENDING,
        parent_id=None,
        child_ids=set(),
    )


@pytest.fixture
def repository(tmp_path: Path) -> DocumentRepository:
    """Create a test repository."""
    return DocumentRepository(tmp_path / "documents")


def test_create_and_get(repository: DocumentRepository, test_doc: Document) -> None:
    """Test creating and retrieving a document."""
    # Create document
    repository.create(test_doc)

    # Get document
    retrieved = repository.get(test_doc.id)

    # Verify
    assert retrieved.id == test_doc.id
    assert retrieved.content == test_doc.content
    assert retrieved.metadata.title == test_doc.metadata.title
    assert retrieved.status == test_doc.status


def test_create_duplicate(repository: DocumentRepository, test_doc: Document) -> None:
    """Test creating a duplicate document."""
    repository.create(test_doc)

    with pytest.raises(DocumentExistsError):
        repository.create(test_doc)


def test_update(repository: DocumentRepository, test_doc: Document) -> None:
    """Test updating a document."""
    # Create document
    repository.create(test_doc)

    # Update document
    test_doc.content = "updated content"
    test_doc.status = DocumentStatus.COMPLETED
    repository.update(test_doc)

    # Verify
    updated = repository.get(test_doc.id)
    assert updated.content == "updated content"
    assert updated.status == DocumentStatus.COMPLETED


def test_update_nonexistent(repository: DocumentRepository, test_doc: Document) -> None:
    """Test updating a nonexistent document."""
    with pytest.raises(DocumentNotFoundError):
        repository.update(test_doc)


def test_delete(repository: DocumentRepository, test_doc: Document) -> None:
    """Test deleting a document."""
    # Create document
    repository.create(test_doc)

    # Verify exists
    assert repository.exists(test_doc.id)

    # Delete
    repository.delete(test_doc.id)

    # Verify gone
    assert not repository.exists(test_doc.id)


def test_delete_nonexistent(repository: DocumentRepository) -> None:
    """Test deleting a nonexistent document."""
    with pytest.raises(DocumentNotFoundError):
        repository.delete(uuid4())


def test_exists(repository: DocumentRepository, test_doc: Document) -> None:
    """Test exists check."""
    assert not repository.exists(test_doc.id)

    repository.create(test_doc)
    assert repository.exists(test_doc.id)


def test_list_ids(repository: DocumentRepository) -> None:
    """Test listing document IDs."""
    # Create some documents
    docs = [
        Document(
            id=uuid4(),
            content=f"test {i}",
            metadata=DocumentMetadata(
                title=f"Test {i}",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                source="test",
            ),
            status=DocumentStatus.PENDING,
        )
        for i in range(3)
    ]

    for doc in docs:
        repository.create(doc)

    # Get IDs
    ids = repository.list_ids()

    # Verify
    assert len(ids) == 3
    assert all(doc.id in ids for doc in docs)


def test_batch_create(repository: DocumentRepository) -> None:
    """Test batch creating documents."""
    # Create test documents
    docs = [
        Document(
            id=uuid4(),
            content=f"test {i}",
            metadata=DocumentMetadata(
                title=f"Test {i}",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                source="test",
            ),
            status=DocumentStatus.PENDING,
        )
        for i in range(3)
    ]

    # Batch create
    repository.batch_create(docs)

    # Verify all exist
    for doc in docs:
        assert repository.exists(doc.id)
        stored = repository.get(doc.id)
        assert stored.content == doc.content


def test_batch_update(repository: DocumentRepository) -> None:
    """Test batch updating documents."""
    # Create test documents
    docs = [
        Document(
            id=uuid4(),
            content=f"test {i}",
            metadata=DocumentMetadata(
                title=f"Test {i}",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                source="test",
            ),
            status=DocumentStatus.PENDING,
        )
        for i in range(3)
    ]

    # Create documents
    repository.batch_create(docs)

    # Update documents
    for doc in docs:
        doc.status = DocumentStatus.COMPLETED

    # Batch update
    repository.batch_update(docs)

    # Verify updates
    for doc in docs:
        stored = repository.get(doc.id)
        assert stored.status == DocumentStatus.COMPLETED


def test_batch_delete(repository: DocumentRepository) -> None:
    """Test batch deleting documents."""
    # Create test documents
    docs = [
        Document(
            id=uuid4(),
            content=f"test {i}",
            metadata=DocumentMetadata(
                title=f"Test {i}",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                source="test",
            ),
            status=DocumentStatus.PENDING,
        )
        for i in range(3)
    ]

    # Create documents
    repository.batch_create(docs)

    # Batch delete
    repository.batch_delete(doc.id for doc in docs)

    # Verify all gone
    for doc in docs:
        assert not repository.exists(doc.id)
