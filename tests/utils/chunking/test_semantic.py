"""Tests for semantic relationship detection.

These tests verify the functionality of semantic processing, including
configuration, embeddings, and relationship detection.
"""
from unittest.mock import Mock, patch
from uuid import uuid4

import numpy as np
import pytest

from src.utils.chunking.references import ReferenceManager, ReferenceType
from src.utils.chunking.semantic import SemanticConfig, SemanticProcessor


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing."""
    base = np.array([0.1, 0.2, 0.3, 0.4])
    embeddings = {'intro': base, 'similar': base * 0.99, 'related': base * 0.7, 'unrelated': -base}
    return {k: v / np.linalg.norm(v) for k, v in embeddings.items()}

@pytest.fixture
def mock_openai():
    """Mock OpenAI embeddings API."""
    with patch('openai.embeddings.create') as mock:
        yield mock

@pytest.fixture
def semantic_processor(mock_openai, mock_embeddings):
    """Create a SemanticProcessor with mocked embeddings."""
    ref_manager = ReferenceManager()
    processor = SemanticProcessor(ref_manager)

    def mock_get_embedding(text):
        key = text.split()[0].lower()
        embedding = mock_embeddings.get(key, mock_embeddings['unrelated'])
        return Mock(data=[Mock(embedding=embedding.tolist())])
    mock_openai.side_effect = mock_get_embedding
    return processor

def test_semantic_config_validation():
    """Test validation of semantic configuration parameters."""
    config = SemanticConfig(similarity_threshold=0.8, max_similar_chunks=3, min_context_score=0.6)
    assert config.similarity_threshold == 0.8
    assert config.max_similar_chunks == 3
    assert config.min_context_score == 0.6
    with pytest.raises(ValueError, match='similarity_threshold must be between 0 and 1'):
        SemanticConfig(similarity_threshold=1.5)
    with pytest.raises(ValueError, match='max_similar_chunks must be positive'):
        SemanticConfig(max_similar_chunks=0)
    with pytest.raises(ValueError, match='min_context_score must be between 0 and 1'):
        SemanticConfig(min_context_score=-0.1)

def test_embedding_caching(semantic_processor, mock_openai):
    """Test that embeddings are properly cached."""
    chunk_id = semantic_processor.ref_manager.add_chunk('intro text')
    embedding1 = semantic_processor.get_chunk_embedding(chunk_id)
    assert mock_openai.call_count == 1
    embedding2 = semantic_processor.get_chunk_embedding(chunk_id)
    assert mock_openai.call_count == 1
    assert np.array_equal(embedding1, embedding2)

def test_similarity_computation(semantic_processor):
    """Test computation of chunk similarities."""
    chunk1 = semantic_processor.ref_manager.add_chunk('intro text')
    chunk2 = semantic_processor.ref_manager.add_chunk('similar text')
    chunk3 = semantic_processor.ref_manager.add_chunk('unrelated text')
    sim1_2 = semantic_processor.compute_similarity(chunk1, chunk2)
    sim1_3 = semantic_processor.compute_similarity(chunk1, chunk3)
    assert sim1_2 > 0.9
    assert sim1_3 < 0.1

def test_find_similar_chunks(semantic_processor):
    """Test finding similar chunks based on content."""
    intro = semantic_processor.ref_manager.add_chunk('intro text')
    similar = semantic_processor.ref_manager.add_chunk('similar text')
    semantic_processor.ref_manager.add_chunk('related text')
    semantic_processor.ref_manager.add_chunk('unrelated text')
    similar_chunks = semantic_processor.find_similar_chunks(intro)
    assert len(similar_chunks) > 0
    assert similar_chunks[0][0] == similar
    scores = [score for _, score in similar_chunks]
    assert all((scores[i] >= scores[i + 1] for i in range(len(scores) - 1)))

def test_semantic_relationship_detection(semantic_processor):
    """Test detection of different types of semantic relationships."""
    intro = semantic_processor.ref_manager.add_chunk('intro text')
    similar = semantic_processor.ref_manager.add_chunk('similar text')
    semantic_processor.ref_manager.add_chunk('related text')
    semantic_processor.ref_manager.add_chunk('unrelated text')
    relationships = semantic_processor.detect_semantic_relationships(intro)
    assert ReferenceType.SIMILAR in relationships
    assert ReferenceType.CONTEXT in relationships
    assert ReferenceType.RELATED in relationships
    similar_chunks = {chunk_id for chunk_id, _ in relationships[ReferenceType.SIMILAR]}
    assert similar in similar_chunks
    for ref_type, chunks in relationships.items():
        for _, score in chunks:
            if ref_type == ReferenceType.SIMILAR:
                assert score >= semantic_processor.config.similarity_threshold
            elif ref_type == ReferenceType.CONTEXT:
                assert semantic_processor.config.min_context_score <= score < semantic_processor.config.similarity_threshold

def test_create_semantic_references(semantic_processor):
    """Test creation of references based on semantic relationships."""
    intro = semantic_processor.ref_manager.add_chunk('intro text')
    semantic_processor.ref_manager.add_chunk('similar text')
    semantic_processor.ref_manager.add_chunk('related text')
    created_refs = semantic_processor.create_semantic_references(intro)
    assert len(created_refs) > 0
    for chunk_id, ref_type, score in created_refs:
        refs = semantic_processor.ref_manager.get_references(intro, ref_type)
        assert chunk_id in refs
        back_refs = semantic_processor.ref_manager.get_references(chunk_id)
        assert intro in back_refs
        ref = semantic_processor.ref_manager._references[intro, chunk_id]
        assert 'similarity_score' in ref.metadata
        assert ref.metadata['similarity_score'] == score

def test_error_handling(semantic_processor):
    """Test error handling in semantic processing."""
    invalid_id = uuid4()
    with pytest.raises(ValueError, match='does not exist'):
        semantic_processor.get_chunk_embedding(invalid_id)
    with pytest.raises(ValueError, match='does not exist'):
        semantic_processor.find_similar_chunks(invalid_id)
    empty_processor = SemanticProcessor(ReferenceManager())
    chunk_id = empty_processor.ref_manager.add_chunk('test text')
    similar_chunks = empty_processor.find_similar_chunks(chunk_id)
    assert len(similar_chunks) == 0

def test_topic_clustering(semantic_processor):
    """Test topic clustering functionality."""
    tech_chunks = [semantic_processor.ref_manager.add_chunk('python programming code development'), semantic_processor.ref_manager.add_chunk('software engineering algorithms'), semantic_processor.ref_manager.add_chunk('machine learning data science')]
    nature_chunks = [semantic_processor.ref_manager.add_chunk('forest trees wildlife nature'), semantic_processor.ref_manager.add_chunk('mountains rivers ecosystem')]
    art_chunks = [semantic_processor.ref_manager.add_chunk('painting drawing sculpture art'), semantic_processor.ref_manager.add_chunk('museum gallery exhibition')]
    all_chunks = set(tech_chunks + nature_chunks + art_chunks)
    topics = semantic_processor.analyze_topic_relationships(all_chunks, num_topics=3)
    assert len(topics) == 3
    assert sum((len(chunk_ids) for chunk_ids in topics.values())) == len(all_chunks)
    for topic_label, chunk_ids in topics.items():
        assert len(chunk_ids) > 0
        assert any((term in topic_label.lower() for term in ['art', 'nature', 'programming', 'learning']))

def test_topic_clustering_edge_cases(semantic_processor):
    """Test topic clustering with edge cases."""
    assert semantic_processor.analyze_topic_relationships(set()) == {}
    single_id = semantic_processor.ref_manager.add_chunk('single topic text')
    single_result = semantic_processor.analyze_topic_relationships({single_id}, num_topics=3)
    assert len(single_result) == 1
    assert single_id in next(iter(single_result.values()))
    invalid_id = uuid4()
    valid_id = semantic_processor.ref_manager.add_chunk('valid chunk')
    result = semantic_processor.analyze_topic_relationships({invalid_id, valid_id})
    assert len(result) == 1
    two_chunks = {semantic_processor.ref_manager.add_chunk('first chunk'), semantic_processor.ref_manager.add_chunk('second chunk')}
    result = semantic_processor.analyze_topic_relationships(two_chunks, num_topics=5)
    assert len(result) == 2

def test_topic_label_quality(semantic_processor):
    """Test the quality of generated topic labels."""
    chunks = {semantic_processor.ref_manager.add_chunk('machine learning artificial intelligence neural networks deep learning'), semantic_processor.ref_manager.add_chunk('data science statistics regression analysis modeling'), semantic_processor.ref_manager.add_chunk('computer vision image processing object detection')}
    topics = semantic_processor.analyze_topic_relationships(chunks, num_topics=2)
    for topic_label in topics:
        assert len(topic_label.split()) >= 4
        assert 'Topic' in topic_label
        assert ':' in topic_label
        terms = topic_label.lower().split(': ')[1].split(', ')
        assert all((len(term) > 0 for term in terms))
        assert len(terms) == 3