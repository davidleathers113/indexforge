"""Tests for document models."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError
import pytest

from src.core.document.models import Document, DocumentMetadata, DocumentRelationship


def test_document_metadata_creation():
    """Test creating document metadata."""
    metadata = DocumentMetadata(
        author="test.user",
        version="1.0.0",
        tags=["test", "document"],
        properties={"category": "test"},
    )

    assert metadata.author == "test.user"
    assert metadata.version == "1.0.0"
    assert metadata.tags == ["test", "document"]
    assert metadata.properties == {"category": "test"}
    assert isinstance(metadata.created_at, datetime)
    assert isinstance(metadata.updated_at, datetime)


def test_document_relationship_creation():
    """Test creating document relationships."""
    source_id = uuid4()
    target_id = uuid4()
    relationship = DocumentRelationship(
        source_id=source_id,
        target_id=target_id,
        relationship_type="reference",
        properties={"weight": "high"},
    )

    assert relationship.source_id == source_id
    assert relationship.target_id == target_id
    assert relationship.relationship_type == "reference"
    assert relationship.properties == {"weight": "high"}
    assert isinstance(relationship.created_at, datetime)


def test_document_creation():
    """Test creating a document."""
    doc_id = uuid4()
    doc = Document(
        id=doc_id,
        content="Test content",
        metadata=DocumentMetadata(author="test.user"),
        relationships=[DocumentRelationship(source_id=doc_id, target_id=uuid4())],
        parent_id=uuid4(),
    )

    assert doc.id == doc_id
    assert doc.content == "Test content"
    assert doc.metadata.author == "test.user"
    assert len(doc.relationships) == 1
    assert doc.parent_id is not None
    assert doc.is_active is True
    assert doc.last_processed is None


def test_document_metadata_defaults():
    """Test document metadata default values."""
    metadata = DocumentMetadata()

    assert metadata.author == ""
    assert metadata.version == "1.0.0"
    assert metadata.tags == []
    assert metadata.properties == {}
    assert (datetime.now(UTC) - metadata.created_at).total_seconds() < 1
    assert (datetime.now(UTC) - metadata.updated_at).total_seconds() < 1


def test_document_relationship_validation():
    """Test document relationship validation."""
    with pytest.raises(ValidationError):
        DocumentRelationship(
            source_id="invalid-uuid",  # type: ignore
            target_id=uuid4(),
        )


def test_document_validation():
    """Test document validation."""
    with pytest.raises(ValidationError):
        Document(
            id="invalid-uuid",  # type: ignore
            content=123,  # type: ignore
        )
