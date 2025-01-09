"""Tests for cross-reference functionality between document chunks."""
import numpy as np
import pytest
from src.cross_reference import ChunkReference, CrossReferenceManager, ReferenceType

@pytest.fixture
def sample_embeddings():
    """Create sample chunk embeddings for testing."""
    rng = np.random.RandomState(42)
    embeddings = {f'chunk_{i}': rng.rand(10) for i in range(5)}
    embeddings['chunk_1'] = embeddings['chunk_2'] * 0.9 + rng.rand(10) * 0.1
    return embeddings

@pytest.fixture
def reference_manager():
    """Create a CrossReferenceManager instance."""
    return CrossReferenceManager(similarity_threshold=0.75, max_semantic_refs=3, n_topics=2)

def test_add_chunk(reference_manager, sample_embeddings):
    """Test adding chunks to the manager."""
    chunk_id = 'chunk_0'
    embedding = sample_embeddings[chunk_id]
    reference_manager.add_chunk(chunk_id, embedding)
    assert chunk_id in reference_manager.references
    assert chunk_id in reference_manager.embeddings
    assert len(reference_manager.references[chunk_id]) == 0
    np.testing.assert_array_equal(reference_manager.embeddings[chunk_id], embedding)

def test_establish_sequential_references(reference_manager):
    """Test establishing sequential references between chunks."""
    chunk_ids = ['chunk_0', 'chunk_1', 'chunk_2']
    for chunk_id in chunk_ids:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))
    reference_manager.establish_sequential_references(chunk_ids)
    refs = reference_manager.get_references('chunk_0', ReferenceType.SEQUENTIAL)
    assert len(refs) == 1
    assert refs[0][0] == 'chunk_1'
    refs = reference_manager.get_references('chunk_1', ReferenceType.SEQUENTIAL)
    assert len(refs) == 2
    assert {ref[0] for ref in refs} == {'chunk_0', 'chunk_2'}

def test_establish_semantic_references(reference_manager, sample_embeddings):
    """Test establishing semantic references based on similarity."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)
    reference_manager.establish_semantic_references()
    refs = reference_manager.get_references('chunk_1', ReferenceType.SEMANTIC)
    assert any((ref[0] == 'chunk_2' for ref in refs))
    refs = reference_manager.get_references('chunk_2', ReferenceType.SEMANTIC)
    assert any((ref[0] == 'chunk_1' for ref in refs))

def test_establish_topic_references(reference_manager, sample_embeddings):
    """Test establishing topic-based references using clustering."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)
    reference_manager.establish_topic_references()
    assert reference_manager.topic_clusters is not None
    all_refs = []
    for chunk_id in sample_embeddings:
        refs = reference_manager.get_references(chunk_id, ReferenceType.TOPIC)
        all_refs.extend(refs)
    assert len(all_refs) > 0

def test_validate_references_circular(reference_manager):
    """Test detection of circular references."""
    chunks = ['chunk_0', 'chunk_1', 'chunk_2']
    for chunk_id in chunks:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))
    reference_manager._add_bidirectional_reference('chunk_0', 'chunk_1', ReferenceType.SEQUENTIAL)
    reference_manager._add_bidirectional_reference('chunk_1', 'chunk_2', ReferenceType.SEQUENTIAL)
    reference_manager._add_bidirectional_reference('chunk_2', 'chunk_0', ReferenceType.SEQUENTIAL)
    errors = reference_manager.validate_references()
    assert any(('Circular reference detected' in error for error in errors))

def test_validate_references_orphaned(reference_manager):
    """Test detection of orphaned references."""
    reference_manager.add_chunk('chunk_0', np.random.rand(10))
    reference_manager.references['chunk_0'].append(ChunkReference(source_id='chunk_0', target_id='non_existent', ref_type=ReferenceType.SEQUENTIAL))
    errors = reference_manager.validate_references()
    assert any(('Orphaned reference' in error for error in errors))

def test_validate_references_missing_backref(reference_manager):
    """Test detection of missing back-references."""
    for chunk_id in ['chunk_0', 'chunk_1']:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))
    reference_manager.references['chunk_0'].append(ChunkReference(source_id='chunk_0', target_id='chunk_1', ref_type=ReferenceType.SEQUENTIAL))
    errors = reference_manager.validate_references()
    assert any(('Missing back-reference' in error for error in errors))

def test_get_references_filtered(reference_manager, sample_embeddings):
    """Test getting filtered references by type."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)
    reference_manager.establish_sequential_references(list(sample_embeddings.keys()))
    reference_manager.establish_semantic_references()
    reference_manager.establish_topic_references()
    chunk_id = 'chunk_1'
    sequential_refs = reference_manager.get_references(chunk_id, ReferenceType.SEQUENTIAL)
    semantic_refs = reference_manager.get_references(chunk_id, ReferenceType.SEMANTIC)
    topic_refs = reference_manager.get_references(chunk_id, ReferenceType.TOPIC)
    assert all((ref[1] == ReferenceType.SEQUENTIAL for ref in sequential_refs))
    assert all((ref[1] == ReferenceType.SEMANTIC for ref in semantic_refs))
    assert all((ref[1] == ReferenceType.TOPIC for ref in topic_refs))

def test_get_topic_cluster(reference_manager, sample_embeddings):
    """Test getting topic cluster for a chunk."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)
    reference_manager.establish_topic_references()
    topic_id = reference_manager.get_topic_cluster('chunk_0')
    assert isinstance(topic_id, int)
    assert 0 <= topic_id < reference_manager.n_topics