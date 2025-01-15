"""Tests for the cross-referencing system.

These tests verify the functionality of the reference management system,
including reference types, bi-directional relationships, and validation.
"""
from uuid import UUID, uuid4

import pytest

from src.utils.chunking.references import ReferenceManager, ReferenceType


@pytest.fixture
def ref_manager():
    """Create a fresh ReferenceManager for each test."""
    return ReferenceManager()

@pytest.fixture
def sample_chunks(ref_manager):
    """Create sample chunks for testing."""
    chunks = {'intro': ref_manager.add_chunk('Introduction section'), 'body1': ref_manager.add_chunk('First body section'), 'body2': ref_manager.add_chunk('Second body section'), 'conclusion': ref_manager.add_chunk('Conclusion section')}
    return chunks

def test_add_chunk_generates_uuid(ref_manager):
    """Test that adding a chunk without ID generates a valid UUID."""
    chunk_id = ref_manager.add_chunk('Test content')
    assert isinstance(chunk_id, UUID)

def test_add_chunk_with_custom_id(ref_manager):
    """Test adding a chunk with a custom UUID."""
    custom_id = uuid4()
    chunk_id = ref_manager.add_chunk('Test content', chunk_id=custom_id)
    assert chunk_id == custom_id

def test_add_duplicate_chunk_id(ref_manager):
    """Test that adding a chunk with existing ID raises error."""
    chunk_id = uuid4()
    ref_manager.add_chunk('First content', chunk_id=chunk_id)
    with pytest.raises(ValueError, match='already exists'):
        ref_manager.add_chunk('Second content', chunk_id=chunk_id)

def test_add_bidirectional_reference(ref_manager, sample_chunks):
    """Test creation of bidirectional references."""
    ref_manager.add_reference(sample_chunks['intro'], sample_chunks['body1'], ReferenceType.NEXT)
    next_refs = ref_manager.get_references(sample_chunks['intro'], ReferenceType.NEXT)
    assert sample_chunks['body1'] in next_refs
    prev_refs = ref_manager.get_references(sample_chunks['body1'], ReferenceType.PREVIOUS)
    assert sample_chunks['intro'] in prev_refs

def test_add_unidirectional_reference(ref_manager, sample_chunks):
    """Test creation of unidirectional references."""
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['intro'], ReferenceType.CITATION, bidirectional=False)
    citations = ref_manager.get_references(sample_chunks['body1'], ReferenceType.CITATION)
    assert sample_chunks['intro'] in citations
    back_refs = ref_manager.get_references(sample_chunks['intro'])
    assert sample_chunks['body1'] not in back_refs

def test_parent_child_references(ref_manager, sample_chunks):
    """Test parent-child relationship references."""
    ref_manager.add_reference(sample_chunks['intro'], sample_chunks['body1'], ReferenceType.PARENT)
    children = ref_manager.get_references(sample_chunks['intro'], ReferenceType.PARENT)
    assert sample_chunks['body1'] in children
    parents = ref_manager.get_references(sample_chunks['body1'], ReferenceType.CHILD)
    assert sample_chunks['intro'] in parents

def test_remove_reference(ref_manager, sample_chunks):
    """Test removal of references."""
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.NEXT)
    ref_manager.remove_reference(sample_chunks['body1'], sample_chunks['body2'])
    assert not ref_manager.get_references(sample_chunks['body1'])
    assert not ref_manager.get_references(sample_chunks['body2'])

def test_remove_specific_reference_type(ref_manager, sample_chunks):
    """Test removal of specific reference type."""
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.NEXT)
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.SIMILAR)
    ref_manager.remove_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.NEXT)
    similar_refs = ref_manager.get_references(sample_chunks['body1'], ReferenceType.SIMILAR)
    assert sample_chunks['body2'] in similar_refs

def test_reference_validation(ref_manager, sample_chunks):
    """Test reference validation functionality."""
    ref_manager.add_reference(sample_chunks['intro'], sample_chunks['body1'], ReferenceType.NEXT)
    assert not ref_manager.validate_references()
    invalid_id = uuid4()
    ref_manager._references[invalid_id, sample_chunks['body1']] = None
    issues = ref_manager.validate_references()
    assert any(('non-existent chunk' in issue for issue in issues))

def test_reference_metadata(ref_manager, sample_chunks):
    """Test reference metadata handling."""
    metadata = {'confidence': 0.95, 'source': 'automatic'}
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.SIMILAR, metadata=metadata)
    ref = ref_manager._references[sample_chunks['body1'], sample_chunks['body2']]
    assert ref.metadata['confidence'] == 0.95
    assert ref.metadata['source'] == 'automatic'

def test_get_all_references(ref_manager, sample_chunks):
    """Test retrieving all references for a chunk."""
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['intro'], ReferenceType.CITATION)
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['body2'], ReferenceType.NEXT)
    ref_manager.add_reference(sample_chunks['body1'], sample_chunks['conclusion'], ReferenceType.SIMILAR)
    all_refs = ref_manager.get_references(sample_chunks['body1'])
    assert len(all_refs) == 3
    assert sample_chunks['intro'] in all_refs
    assert sample_chunks['body2'] in all_refs
    assert sample_chunks['conclusion'] in all_refs

def test_error_handling(ref_manager, sample_chunks):
    """Test error handling for invalid operations."""
    invalid_id = uuid4()
    with pytest.raises(ValueError, match='does not exist'):
        ref_manager.add_reference(invalid_id, sample_chunks['body1'], ReferenceType.NEXT)
    with pytest.raises(ValueError, match='does not exist'):
        ref_manager.add_reference(sample_chunks['body1'], invalid_id, ReferenceType.NEXT)
    with pytest.raises(ValueError, match='No reference exists'):
        ref_manager.remove_reference(sample_chunks['body1'], sample_chunks['body2'])

def test_circular_reference_prevention(ref_manager):
    """Test prevention of self-referential chunks."""
    chunk_id = ref_manager.add_chunk('Test content')
    with pytest.raises(ValueError, match='Self-referential'):
        ref_manager.add_reference(chunk_id, chunk_id, ReferenceType.SIMILAR)