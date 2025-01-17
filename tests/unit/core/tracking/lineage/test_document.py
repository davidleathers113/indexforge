"""Unit tests for document lineage tracking functionality."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.tracking.lineage import DocumentLineageTracker
from src.core.tracking.models import DocumentLineage


@pytest.fixture
def mock_storage():
    """Create a mock storage backend."""
    storage = MagicMock()
    storage.get_lineage.return_value = None
    storage.save_lineage.return_value = None
    return storage


@pytest.fixture
def sample_doc():
    """Create a sample document lineage object."""
    return DocumentLineage(
        doc_id="doc-1",
        origin_id="origin-1",
        origin_source="test-source",
        origin_type="test-type",
        metadata={"test": "metadata"},
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )


@pytest.fixture
def tracker(mock_storage):
    """Create a DocumentLineageTracker instance with mock storage."""
    return DocumentLineageTracker(mock_storage)


def test_get_ancestors_document_not_found(tracker):
    """Test getting ancestors for nonexistent document."""
    with pytest.raises(ValueError, match="Document not found: doc-1"):
        tracker.get_ancestors("doc-1")


def test_get_ancestors_no_parents(tracker, sample_doc):
    """Test getting ancestors for document with no parents."""
    tracker.storage.get_lineage.return_value = sample_doc
    ancestors = tracker.get_ancestors("doc-1")
    assert not ancestors
    tracker.storage.get_lineage.assert_called_with("doc-1")


def test_get_ancestors_with_parents(tracker, sample_doc):
    """Test getting ancestors for document with parents."""
    parent_doc = DocumentLineage(
        doc_id="parent-1",
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    sample_doc.parents = ["parent-1"]

    def mock_get_lineage(doc_id):
        return {
            "doc-1": sample_doc,
            "parent-1": parent_doc,
        }.get(doc_id)

    tracker.storage.get_lineage.side_effect = mock_get_lineage
    ancestors = tracker.get_ancestors("doc-1")
    assert ancestors == {"parent-1"}


def test_get_descendants_document_not_found(tracker):
    """Test getting descendants for nonexistent document."""
    with pytest.raises(ValueError, match="Document not found: doc-1"):
        tracker.get_descendants("doc-1")


def test_get_descendants_no_children(tracker, sample_doc):
    """Test getting descendants for document with no children."""
    tracker.storage.get_lineage.return_value = sample_doc
    descendants = tracker.get_descendants("doc-1")
    assert not descendants
    tracker.storage.get_lineage.assert_called_with("doc-1")


def test_get_descendants_with_children(tracker, sample_doc):
    """Test getting descendants for document with children."""
    child_doc = DocumentLineage(
        doc_id="child-1",
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    sample_doc.children = ["child-1"]

    def mock_get_lineage(doc_id):
        return {
            "doc-1": sample_doc,
            "child-1": child_doc,
        }.get(doc_id)

    tracker.storage.get_lineage.side_effect = mock_get_lineage
    descendants = tracker.get_descendants("doc-1")
    assert descendants == {"child-1"}


def test_add_parent_document_not_found(tracker):
    """Test adding parent when child document doesn't exist."""
    with pytest.raises(ValueError, match="Child document not found: doc-1"):
        tracker.add_parent("doc-1", "parent-1")


def test_add_parent_parent_not_found(tracker, sample_doc):
    """Test adding parent when parent document doesn't exist."""
    tracker.storage.get_lineage.side_effect = lambda doc_id: (
        sample_doc if doc_id == "doc-1" else None
    )
    with pytest.raises(ValueError, match="Parent document not found: parent-1"):
        tracker.add_parent("doc-1", "parent-1")


@patch("src.core.tracking.validation.strategies.validate_no_circular_reference")
def test_add_parent_circular_reference(mock_validate, tracker, sample_doc):
    """Test adding parent that would create circular reference."""
    parent_doc = DocumentLineage(
        doc_id="parent-1",
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    tracker.storage.get_lineage.side_effect = lambda doc_id: (
        sample_doc if doc_id == "doc-1" else parent_doc
    )
    mock_validate.return_value = True

    with pytest.raises(ValueError, match="Circular reference detected"):
        tracker.add_parent("doc-1", "parent-1")


@patch("src.core.tracking.validation.strategies.validate_no_circular_reference")
def test_add_parent_success(mock_validate, tracker, sample_doc):
    """Test successfully adding parent relationship."""
    parent_doc = DocumentLineage(
        doc_id="parent-1",
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )
    tracker.storage.get_lineage.side_effect = lambda doc_id: (
        sample_doc if doc_id == "doc-1" else parent_doc
    )
    mock_validate.return_value = False

    tracker.add_parent("doc-1", "parent-1")

    assert "parent-1" in sample_doc.parents
    assert "doc-1" in parent_doc.children
    assert "doc-1" in parent_doc.derived_documents
    assert sample_doc.derived_from == "parent-1"
    assert tracker.storage.save_lineage.call_count == 2


def test_remove_parent_document_not_found(tracker):
    """Test removing parent when child document doesn't exist."""
    with pytest.raises(ValueError, match="Child document not found: doc-1"):
        tracker.remove_parent("doc-1", "parent-1")


def test_remove_parent_parent_not_found(tracker, sample_doc):
    """Test removing parent when parent document doesn't exist."""
    tracker.storage.get_lineage.side_effect = lambda doc_id: (
        sample_doc if doc_id == "doc-1" else None
    )
    with pytest.raises(ValueError, match="Parent document not found: parent-1"):
        tracker.remove_parent("doc-1", "parent-1")


def test_remove_parent_success(tracker, sample_doc):
    """Test successfully removing parent relationship."""
    parent_doc = DocumentLineage(
        doc_id="parent-1",
        created_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
        children=["doc-1"],
        derived_documents=["doc-1"],
    )
    sample_doc.parents = ["parent-1"]
    sample_doc.derived_from = "parent-1"

    tracker.storage.get_lineage.side_effect = lambda doc_id: (
        sample_doc if doc_id == "doc-1" else parent_doc
    )

    tracker.remove_parent("doc-1", "parent-1")

    assert not sample_doc.parents
    assert not sample_doc.derived_from
    assert not parent_doc.children
    assert not parent_doc.derived_documents
    assert tracker.storage.save_lineage.call_count == 2


def test_get_lineage_info_document_not_found(tracker):
    """Test getting lineage info for nonexistent document."""
    with pytest.raises(ValueError, match="Document not found: doc-1"):
        tracker.get_lineage_info("doc-1")


def test_get_lineage_info_success(tracker, sample_doc):
    """Test successfully getting lineage info."""
    tracker.storage.get_lineage.return_value = sample_doc

    with patch.object(tracker, "get_ancestors") as mock_ancestors:
        with patch.object(tracker, "get_descendants") as mock_descendants:
            mock_ancestors.return_value = {"parent-1"}
            mock_descendants.return_value = {"child-1"}

            info = tracker.get_lineage_info("doc-1")

            assert info["ancestors"] == {"parent-1"}
            assert info["descendants"] == {"child-1"}
            assert info["metadata"] == sample_doc.metadata
            assert info["created_at"] == sample_doc.created_at
            assert info["last_modified"] == sample_doc.last_modified
            assert info["origin_id"] == sample_doc.origin_id
            assert info["origin_source"] == sample_doc.origin_source
            assert info["origin_type"] == sample_doc.origin_type
