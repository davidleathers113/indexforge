"""Tests for search operations module."""
import json
from pathlib import Path
from src.pipeline.search import SearchOperations

def load_sample_documents():
    """Load sample documents from JSON file."""
    json_path = Path(__file__).parent.parent.parent / 'data' / 'sample_documents.json'
    with open(json_path) as f:
        data = json.load(f)
    return list(data.values())

def test_search_initialization(mock_search_components):
    """Test SearchOperations initialization"""
    search_ops = SearchOperations(**mock_search_components)
    emb_gen = mock_search_components['embedding_generator']
    vector_index = mock_search_components['vector_index']
    topic_clust = mock_search_components['topic_clusterer']
    logger = mock_search_components['logger']
    assert search_ops.embedding_generator == emb_gen
    assert search_ops.vector_index == vector_index
    assert search_ops.topic_clusterer == topic_clust
    assert search_ops.logger == logger

def test_text_only_search(mock_search_components):
    """Test search with text query only"""
    search_ops = SearchOperations(**mock_search_components)
    query_text = 'test query'
    query_vector = [0.1, 0.2, 0.3]
    expected_results = [{'id': '1', 'score': 0.9}]
    emb_gen = mock_search_components['embedding_generator']
    vector_index = mock_search_components['vector_index']
    emb_gen._get_embedding.return_value = query_vector
    vector_index.hybrid_search.return_value = expected_results
    results = search_ops.search(query_text=query_text)
    emb_gen._get_embedding.assert_called_once_with(query_text)
    vector_index.hybrid_search.assert_called_once_with(text_query=query_text, query_vector=query_vector, limit=10)
    assert results == expected_results

def test_vector_only_search(mock_search_components):
    """Test search with vector query only"""
    search_ops = SearchOperations(**mock_search_components)
    query_vector = [0.1, 0.2, 0.3]
    expected_results = [{'id': '1', 'score': 0.9}]
    vector_index = mock_search_components['vector_index']
    vector_index.semantic_search.return_value = expected_results
    results = search_ops.search(query_text='', query_vector=query_vector, use_hybrid=False)
    vector_index.semantic_search.assert_called_once_with(query_vector=query_vector, limit=10, min_score=0.7)
    assert results == expected_results

def test_hybrid_search(mock_search_components):
    """Test hybrid search with both text and vector"""
    search_ops = SearchOperations(**mock_search_components)
    query_text = 'test query'
    query_vector = [0.1, 0.2, 0.3]
    expected_results = [{'id': '1', 'score': 0.9}]
    vector_index = mock_search_components['vector_index']
    vector_index.hybrid_search.return_value = expected_results
    results = search_ops.search(query_text=query_text, query_vector=query_vector, use_hybrid=True)
    vector_index.hybrid_search.assert_called_once_with(text_query=query_text, query_vector=query_vector, limit=10)
    assert results == expected_results

def test_search_with_custom_parameters(mock_search_components):
    """Test search with custom limit and min_score"""
    search_ops = SearchOperations(**mock_search_components)
    query_vector = [0.1, 0.2, 0.3]
    expected_results = [{'id': '1', 'score': 0.9}]
    vector_index = mock_search_components['vector_index']
    vector_index.semantic_search.return_value = expected_results
    results = search_ops.search(query_text='', query_vector=query_vector, limit=5, min_score=0.8, use_hybrid=False)
    vector_index.semantic_search.assert_called_once_with(query_vector=query_vector, limit=5, min_score=0.8)
    assert results == expected_results

def test_search_error_handling(mock_search_components):
    """Test error handling in search operations"""
    search_ops = SearchOperations(**mock_search_components)
    emb_gen = mock_search_components['embedding_generator']
    logger = mock_search_components['logger']
    emb_gen._get_embedding.side_effect = Exception('Test error')
    results = search_ops.search(query_text='test query')
    assert results == []
    logger.error.assert_called_once()

def test_invalid_search_criteria(mock_search_components):
    """Test search with invalid criteria"""
    search_ops = SearchOperations(**mock_search_components)
    logger = mock_search_components['logger']
    results = search_ops.search(query_text='')
    assert results == []
    logger.error.assert_called_once_with('No valid search criteria provided')

def test_find_similar_topics(mock_search_components):
    """Test finding similar topics"""
    search_ops = SearchOperations(**mock_search_components)
    query_text = 'test topic'
    query_vector = [0.1, 0.2, 0.3]
    expected_results = [{'topic': 'Topic 1', 'score': 0.9}]
    sample_documents = load_sample_documents()
    emb_gen = mock_search_components['embedding_generator']
    topic_clust = mock_search_components['topic_clusterer']
    emb_gen._get_embedding.return_value = query_vector
    topic_clust.find_similar_topics.return_value = expected_results
    results = search_ops.find_similar_topics(query_text=query_text, documents=sample_documents, top_k=3)
    emb_gen._get_embedding.assert_called_once_with(query_text)
    topic_clust.find_similar_topics.assert_called_once_with(query_vector=query_vector, documents=sample_documents, top_k=3)
    assert results == expected_results

def test_find_similar_topics_error(mock_search_components):
    """Test error handling in topic similarity search"""
    search_ops = SearchOperations(**mock_search_components)
    emb_gen = mock_search_components['embedding_generator']
    logger = mock_search_components['logger']
    sample_documents = load_sample_documents()
    emb_gen._get_embedding.side_effect = Exception('Test error')
    results = search_ops.find_similar_topics(query_text='test', documents=sample_documents)
    assert results == []
    logger.error.assert_called_once()

def test_empty_documents_topic_search(mock_search_components):
    """Test topic search with empty document list"""
    search_ops = SearchOperations(**mock_search_components)
    query_vector = [0.1, 0.2, 0.3]
    expected_results = []
    emb_gen = mock_search_components['embedding_generator']
    topic_clust = mock_search_components['topic_clusterer']
    emb_gen._get_embedding.return_value = query_vector
    topic_clust.find_similar_topics.return_value = expected_results
    results = search_ops.find_similar_topics(query_text='test', documents=[])
    assert results == expected_results
    topic_clust.find_similar_topics.assert_called_once_with(query_vector=query_vector, documents=[], top_k=5)