"""Tests for lineage operations functionality."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import add_document
from src.connectors.direct_documentation_indexing.source_tracking.enums import ProcessingStatus
from src.connectors.direct_documentation_indexing.source_tracking.lineage_operations import get_derivation_chain
from src.connectors.direct_documentation_indexing.source_tracking.models import DocumentLineage
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage
from src.connectors.direct_documentation_indexing.source_tracking.validation import validate_lineage_relationships

@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / 'lineage'

@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))

def test_add_document(storage):
    """Test adding a new document."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    lineage = storage.get_lineage(doc_id)
    assert lineage.doc_id == doc_id
    assert not lineage.parents
    assert not lineage.children

def test_add_document_with_parents(storage):
    """Test adding a document with parent relationships."""
    parent_id = 'parent_doc'
    child_id = 'child_doc'
    add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=[parent_id])
    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)
    assert parent_id in child.parents
    assert child_id in parent.children

def test_get_derivation_chain(storage):
    """Test getting the derivation chain for a document."""
    doc_ids = ['doc1', 'doc2', 'doc3', 'doc4']
    add_document(storage, doc_id=doc_ids[0])
    for i in range(1, len(doc_ids)):
        add_document(storage, doc_id=doc_ids[i], parent_ids=[doc_ids[i - 1]])
    chain = get_derivation_chain(storage, doc_ids[-1])
    assert len(chain) == len(doc_ids)
    assert [doc.doc_id for doc in chain] == list(reversed(doc_ids))

def test_validate_lineage_relationships(storage):
    """Test validation of lineage relationships."""
    doc1_id = 'doc1'
    doc2_id = 'doc2'
    add_document(storage, doc_id=doc1_id)
    add_document(storage, doc_id=doc2_id, parent_ids=[doc1_id])
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert len(errors) == 0
    doc1 = storage.get_lineage(doc1_id)
    doc2 = storage.get_lineage(doc2_id)
    assert doc2_id in doc1.children
    assert doc1_id in doc2.parents

def test_validate_lineage_relationships_with_issues(storage):
    """Test validation of lineage relationships with issues."""
    doc_id = 'child'
    non_existent_parent = 'non_existent_parent'
    with pytest.raises(ValueError) as exc_info:
        add_document(storage, doc_id=doc_id, parent_ids=[non_existent_parent])
    assert f'Parent document {non_existent_parent} not found' in str(exc_info.value)
    add_document(storage, doc_id=doc_id)
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert len(errors) == 0

def test_circular_reference_detection(storage):
    """Test detection of circular references in lineage."""
    doc1_id = 'doc1'
    doc2_id = 'doc2'
    doc3_id = 'doc3'
    add_document(storage, doc_id=doc1_id)
    add_document(storage, doc_id=doc2_id, parent_ids=[doc1_id])
    add_document(storage, doc_id=doc3_id, parent_ids=[doc2_id])
    with pytest.raises(ValueError) as exc_info:
        add_document(storage, doc_id=doc1_id, parent_ids=[doc3_id])
    assert 'circular' in str(exc_info.value).lower()
    doc1 = storage.get_lineage(doc1_id)
    doc2 = storage.get_lineage(doc2_id)
    doc3 = storage.get_lineage(doc3_id)
    assert doc2_id in doc1.children
    assert doc3_id in doc2.children
    assert doc1_id in doc2.parents
    assert doc2_id in doc3.parents

def test_multiple_parents(storage):
    """Test document with multiple parents."""
    parent_ids = ['parent1', 'parent2', 'parent3']
    child_id = 'child'
    for parent_id in parent_ids:
        add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=parent_ids)
    child = storage.get_lineage(child_id)
    assert set(child.parents) == set(parent_ids)
    for parent_id in parent_ids:
        parent = storage.get_lineage(parent_id)
        assert child_id in parent.children

def test_lineage_persistence(temp_lineage_dir):
    """Test persistence of lineage relationships."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    parent_id = 'parent'
    child_id = 'child'
    add_document(storage1, doc_id=parent_id)
    add_document(storage1, doc_id=child_id, parent_ids=[parent_id])
    storage2 = LineageStorage(str(temp_lineage_dir))
    parent = storage2.get_lineage(parent_id)
    child = storage2.get_lineage(child_id)
    assert child_id in parent.children
    assert parent_id in child.parents