"""Tests for document relationship operations."""

from uuid import uuid4

import pytest

from src.core.models.documents import Document, DocumentStatus
from src.core.tracking.storage import DocumentStorage


class TestDocumentRelationships:
    """Test document relationship operations."""

    def test_parent_child_relationship(
        self, storage: DocumentStorage, document_with_parent: Document
    ):
        """Test basic parent-child relationship."""
        storage.save_document(document_with_parent)

        # Verify child document
        retrieved_child = storage.get_document(document_with_parent.id)
        assert retrieved_child is not None
        assert retrieved_child.parent_id is not None

        # Verify parent document
        retrieved_parent = storage.get_document(document_with_parent.parent_id)
        assert retrieved_parent is not None
        assert document_with_parent.id in retrieved_parent.child_ids

    def test_document_chain(self, storage: DocumentStorage, document_chain: list[UUID]):
        """Test chain of document relationships."""
        for i in range(1, len(document_chain)):
            parent = storage.get_document(document_chain[i - 1])
            child = storage.get_document(document_chain[i])

            assert parent is not None
            assert child is not None
            assert child.id in parent.child_ids
            assert child.parent_id == parent.id

    def test_update_parent_relationship(
        self, storage: DocumentStorage, document_with_parent: Document
    ):
        """Test updating document's parent."""
        storage.save_document(document_with_parent)

        # Create new parent
        new_parent = storage.get_document(document_with_parent.parent_id)
        assert new_parent is not None

        # Update parent
        storage.update_document(document_with_parent.id, {"parent_id": new_parent.id})

        # Verify relationships
        updated_doc = storage.get_document(document_with_parent.id)
        updated_parent = storage.get_document(new_parent.id)

        assert updated_doc is not None
        assert updated_parent is not None
        assert updated_doc.parent_id == new_parent.id
        assert updated_doc.id in updated_parent.child_ids

    def test_remove_parent_relationship(
        self, storage: DocumentStorage, document_with_parent: Document
    ):
        """Test removing document's parent."""
        storage.save_document(document_with_parent)

        # Remove parent
        storage.update_document(document_with_parent.id, {"parent_id": None})

        # Verify relationships
        updated_doc = storage.get_document(document_with_parent.id)
        old_parent = storage.get_document(document_with_parent.parent_id)

        assert updated_doc is not None
        assert old_parent is not None
        assert updated_doc.parent_id is None
        assert updated_doc.id not in old_parent.child_ids

    def test_update_nonexistent_parent(
        self, storage: DocumentStorage, document_with_parent: Document
    ):
        """Test updating to nonexistent parent raises error."""
        storage.save_document(document_with_parent)

        with pytest.raises(ValueError):
            storage.update_document(document_with_parent.id, {"parent_id": uuid4()})

    def test_circular_relationship_prevention(
        self, storage: DocumentStorage, document_chain: list[UUID]
    ):
        """Test prevention of circular relationships."""
        # Attempt to create circular reference
        with pytest.raises(ValueError):
            storage.update_document(document_chain[0], {"parent_id": document_chain[-1]})
