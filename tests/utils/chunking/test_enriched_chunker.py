"""Tests for the enriched chunking system.

These tests verify the integration of paragraph-based chunking with
semantic analysis and topic clustering.
"""
import pytest
from src.utils.chunking.base import ChunkingConfig
from src.utils.chunking.enriched_chunker import EnrichedChunker, EnrichedChunkingConfig
from src.utils.chunking.semantic import SemanticConfig

@pytest.fixture
def enriched_chunker():
    """Create an enriched chunker with default configuration."""
    chunking_config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=50, max_chunk_size=150)
    semantic_config = SemanticConfig(similarity_threshold=0.7, min_context_score=0.5, max_similar_chunks=5)
    config = EnrichedChunkingConfig(chunking_config=chunking_config, semantic_config=semantic_config, enable_topic_clustering=True, min_cluster_size=2, max_topics=3)
    return EnrichedChunker(config)

def test_basic_chunking(enriched_chunker):
    """Test basic chunking functionality without semantic enrichment."""
    text = 'This is a test paragraph. It contains multiple sentences. ' * 5
    chunks = enriched_chunker.process_text(text)
    assert len(chunks) > 0
    for chunk in chunks:
        assert 'id' in chunk
        assert 'content' in chunk
        assert 'metadata' in chunk
        assert isinstance(chunk['metadata'], dict)

def test_topic_clustering(enriched_chunker):
    """Test topic clustering and metadata enrichment."""
    texts = ['Python is a programming language. It is used for software development.', 'Machine learning models process data. Neural networks learn patterns.', 'Trees and forests are ecosystems. Wildlife thrives in nature.', 'Mountains and rivers shape landscapes. Natural formations evolve slowly.']
    chunk_groups = enriched_chunker.batch_process_texts(texts)
    topics_found = set()
    for group in chunk_groups:
        for chunk in group:
            if 'topic' in chunk['metadata']:
                topics_found.add(chunk['metadata']['topic'])
    assert len(topics_found) > 0
    assert len(topics_found) <= enriched_chunker.config.max_topics

def test_semantic_relationships(enriched_chunker):
    """Test semantic relationship detection between chunks."""
    text = '\n    Machine learning is a subset of artificial intelligence.\n    Neural networks are used in deep learning applications.\n    Data science involves statistical analysis and modeling.\n    '
    chunks = enriched_chunker.process_text(text)
    relationships_found = False
    for chunk in chunks:
        if 'similar_chunks' in chunk['metadata'] or any((key.startswith('related_') for key in chunk['metadata'])):
            relationships_found = True
            break
    assert relationships_found

def test_batch_processing(enriched_chunker):
    """Test batch processing of multiple texts."""
    texts = ['First document with multiple sentences. More content here.', 'Second document about different topics. Additional information.', 'Third document discussing various subjects. Extra details included.']
    chunk_groups = enriched_chunker.batch_process_texts(texts)
    assert len(chunk_groups) == len(texts)
    for group in chunk_groups:
        assert len(group) > 0
        for chunk in group:
            assert 'id' in chunk
            assert 'content' in chunk
            assert 'metadata' in chunk

def test_configuration_options(enriched_chunker):
    """Test different configuration options."""
    enriched_chunker.config.enable_topic_clustering = False
    text = 'Test content for configuration. Multiple sentences here.' * 3
    chunks = enriched_chunker.process_text(text)
    for chunk in chunks:
        assert 'topic' not in chunk['metadata']
    enriched_chunker.config.add_similarity_metadata = False
    chunks = enriched_chunker.process_text(text)
    for chunk in chunks:
        assert 'similar_chunks' not in chunk['metadata']

def test_edge_cases(enriched_chunker):
    """Test edge cases and error handling."""
    assert len(enriched_chunker.process_text('')) == 0
    short_text = 'Short text.'
    chunks = enriched_chunker.process_text(short_text)
    assert len(chunks) == 1
    assert chunks[0]['content'] == short_text
    results = enriched_chunker.batch_process_texts(['', 'Some content', ''])
    assert len(results) == 3
    assert len(results[0]) == 0
    assert len(results[1]) > 0
    assert len(results[2]) == 0