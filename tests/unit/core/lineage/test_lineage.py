"""Unit tests for document lineage tracking."""

import uuid

from pydantic import ValidationError
import pytest

from src.core.lineage.base import ChangeType, DocumentLineage, SourceInfo
from src.core.lineage.manager import CircularReferenceError, LineageError, LineageManager


@pytest.fixture
def source_info() -> SourceInfo:
    """Create test source information."""
    return SourceInfo(
        source_id="test-source",
        source_type="git",
        location="path/to/doc.md",
        metadata={"branch": "main"},
    )


@pytest.fixture
def document_id() -> uuid.UUID:
    """Create test document ID."""
    return uuid.uuid4()


@pytest.fixture
def lineage_manager() -> LineageManager:
    """Create lineage manager instance."""
    return LineageManager()


@pytest.mark.asyncio
async def test_create_lineage(
    lineage_manager: LineageManager, document_id: uuid.UUID, source_info: SourceInfo
):
    """Test creating new document lineage."""
    lineage = await lineage_manager.create_lineage(document_id, source_info)

    assert isinstance(lineage, DocumentLineage)
    assert lineage.document_id == document_id
    assert lineage.source_info == source_info
    assert lineage.current_version == 1
    assert len(lineage.history) == 1
    assert lineage.history[0].change_type == ChangeType.CREATED


@pytest.mark.asyncio
async def test_create_lineage_with_parent(
    lineage_manager: LineageManager,
    document_id: uuid.UUID,
    source_info: SourceInfo,
):
    """Test creating lineage with parent document."""
    parent_id = uuid.uuid4()

    # Create parent first
    parent = await lineage_manager.create_lineage(parent_id, source_info)
    assert parent.children_ids == set()

    # Create child
    child = await lineage_manager.create_lineage(document_id, source_info, parent_id)
    assert child.parent_id == parent_id

    # Verify parent was updated
    parent = await lineage_manager.get_lineage(parent_id)
    assert document_id in parent.children_ids
    assert len(parent.history) == 2  # Created + Child added


@pytest.mark.asyncio
async def test_create_lineage_invalid_parent(
    lineage_manager: LineageManager,
    document_id: uuid.UUID,
    source_info: SourceInfo,
):
    """Test creating lineage with non-existent parent."""
    with pytest.raises(ValidationError):
        await lineage_manager.create_lineage(document_id, source_info, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_lineage_duplicate(
    lineage_manager: LineageManager,
    document_id: uuid.UUID,
    source_info: SourceInfo,
):
    """Test creating duplicate lineage."""
    await lineage_manager.create_lineage(document_id, source_info)

    with pytest.raises(LineageError):
        await lineage_manager.create_lineage(document_id, source_info)


@pytest.mark.asyncio
async def test_update_lineage(
    lineage_manager: LineageManager, document_id: uuid.UUID, source_info: SourceInfo
):
    """Test updating document lineage."""
    await lineage_manager.create_lineage(document_id, source_info)

    new_source = SourceInfo(
        source_id="new-source",
        source_type="filesystem",
        location="/new/path.md",
        metadata={"key": "value"},
    )

    lineage = await lineage_manager.update_lineage(
        document_id,
        ChangeType.UPDATED,
        new_source,
        metadata={"update_type": "content"},
    )

    assert lineage.current_version == 2
    assert lineage.source_info == new_source
    assert len(lineage.history) == 2
    assert lineage.history[-1].change_type == ChangeType.UPDATED
    assert lineage.history[-1].metadata == {"update_type": "content"}


@pytest.mark.asyncio
async def test_update_lineage_references(lineage_manager: LineageManager):
    """Test updating document references."""
    doc_id = uuid.uuid4()
    ref_id1 = uuid.uuid4()
    ref_id2 = uuid.uuid4()

    # Create documents
    await lineage_manager.create_lineage(doc_id)
    await lineage_manager.create_lineage(ref_id1)
    await lineage_manager.create_lineage(ref_id2)

    # Add references
    doc = await lineage_manager.update_lineage(
        doc_id,
        ChangeType.REFERENCED,
        related_ids={ref_id1, ref_id2},
    )

    assert doc.reference_ids == {ref_id1, ref_id2}

    # Verify referenced documents were updated
    ref1 = await lineage_manager.get_lineage(ref_id1)
    ref2 = await lineage_manager.get_lineage(ref_id2)

    assert doc_id in ref1.referenced_by_ids
    assert doc_id in ref2.referenced_by_ids


@pytest.mark.asyncio
async def test_circular_reference_detection(lineage_manager: LineageManager):
    """Test detection of circular references."""
    doc_id1 = uuid.uuid4()
    doc_id2 = uuid.uuid4()
    doc_id3 = uuid.uuid4()

    # Create documents
    await lineage_manager.create_lineage(doc_id1)
    await lineage_manager.create_lineage(doc_id2)
    await lineage_manager.create_lineage(doc_id3)

    # Create reference chain: doc1 -> doc2 -> doc3
    await lineage_manager.update_lineage(
        doc_id1,
        ChangeType.REFERENCED,
        related_ids={doc_id2},
    )
    await lineage_manager.update_lineage(
        doc_id2,
        ChangeType.REFERENCED,
        related_ids={doc_id3},
    )

    # Attempt to create circular reference: doc3 -> doc1
    with pytest.raises(CircularReferenceError):
        await lineage_manager.update_lineage(
            doc_id3,
            ChangeType.REFERENCED,
            related_ids={doc_id1},
        )


@pytest.mark.asyncio
async def test_delete_lineage(lineage_manager: LineageManager):
    """Test deleting document lineage."""
    doc_id = uuid.uuid4()
    ref_id = uuid.uuid4()
    parent_id = uuid.uuid4()

    # Create documents with relationships
    await lineage_manager.create_lineage(parent_id)
    await lineage_manager.create_lineage(ref_id)
    await lineage_manager.create_lineage(doc_id, parent_id=parent_id)

    await lineage_manager.update_lineage(
        doc_id,
        ChangeType.REFERENCED,
        related_ids={ref_id},
    )

    # Delete document
    await lineage_manager.delete_lineage(doc_id)

    # Verify document was deleted
    assert await lineage_manager.get_lineage(doc_id) is None

    # Verify relationships were cleaned up
    parent = await lineage_manager.get_lineage(parent_id)
    ref = await lineage_manager.get_lineage(ref_id)

    assert doc_id not in parent.children_ids
    assert doc_id not in ref.referenced_by_ids


@pytest.mark.asyncio
async def test_get_document_history(lineage_manager: LineageManager, document_id: uuid.UUID):
    """Test retrieving document history."""
    await lineage_manager.create_lineage(document_id)

    # Make some changes
    await lineage_manager.update_lineage(
        document_id,
        ChangeType.UPDATED,
        metadata={"change": "1"},
    )
    await lineage_manager.update_lineage(
        document_id,
        ChangeType.UPDATED,
        metadata={"change": "2"},
    )

    # Get full history
    history = await lineage_manager.get_document_history(document_id)
    assert len(history) == 3  # Created + 2 updates

    # Get history since version 1
    recent = await lineage_manager.get_document_history(document_id, since_version=1)
    assert len(recent) == 2  # Only the updates


@pytest.mark.asyncio
async def test_get_related_documents(lineage_manager: LineageManager):
    """Test getting all related documents."""
    doc_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    child_id = uuid.uuid4()
    ref_id = uuid.uuid4()
    ref_by_id = uuid.uuid4()

    # Create all documents
    await lineage_manager.create_lineage(parent_id)
    await lineage_manager.create_lineage(ref_id)
    await lineage_manager.create_lineage(ref_by_id)
    await lineage_manager.create_lineage(doc_id, parent_id=parent_id)
    await lineage_manager.create_lineage(child_id, parent_id=doc_id)

    # Add references
    await lineage_manager.update_lineage(
        doc_id,
        ChangeType.REFERENCED,
        related_ids={ref_id},
    )
    await lineage_manager.update_lineage(
        ref_by_id,
        ChangeType.REFERENCED,
        related_ids={doc_id},
    )

    # Get lineage and check related documents
    lineage = await lineage_manager.get_lineage(doc_id)
    related = lineage.get_related_documents()

    assert related == {parent_id, child_id, ref_id, ref_by_id}
