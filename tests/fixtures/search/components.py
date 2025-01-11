"""Search components fixtures."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="function")
def mock_search_manager():
    """Mock search manager for testing."""
    mock = MagicMock(name="vector_index")
    mock.semantic_search.return_value = [{"id": "1", "score": 0.9}]
    mock.hybrid_search.return_value = [{"id": "1", "score": 0.9}]
    return mock


@pytest.fixture(scope="function")
def mock_search_components(mock_search_manager):
    """Mock search components for testing."""
    # Create embedding generator mock
    embedding_generator = MagicMock(name="embedding_generator")
    embedding_generator._get_embedding.return_value = [0.1, 0.2, 0.3]

    # Create topic clusterer mock
    topic_clusterer = MagicMock(name="topic_clusterer")
    topic_clusterer.find_similar_topics.return_value = [{"topic": "Topic 1", "score": 0.9}]

    # Create logger mock
    logger = MagicMock(name="logger")

    # Create components dictionary with only the required components
    return {
        "embedding_generator": embedding_generator,
        "vector_index": mock_search_manager,
        "topic_clusterer": topic_clusterer,
        "logger": logger,
    }


@pytest.fixture(scope="function")
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": f"doc{i}",
            "content": {"body": f"Test document {i}", "metadata": {"title": f"Doc {i}"}},
            "embedding": [0.1 * (j + 1) for j in range(3)],  # 3D vector for testing
        }
        for i in range(1, 4)  # Create 3 sample documents
    ]
