"""Pipeline component mock fixtures."""

from typing import Dict, List
from unittest.mock import DEFAULT, MagicMock, patch

import pytest

from .logger import logger
from .pipeline_state import pipeline_state


def create_pii_detector_mock():
    """Create mock PII detector with logging."""
    mock = MagicMock()

    def detect_with_logging(text):
        logger.debug(f"PIIDetector.detect input: {text}")
        result = []  # Mock PII matches
        logger.debug(f"PIIDetector.detect output: {result}")
        return result

    def analyze_with_logging(doc):
        logger.debug(f"PIIDetector.analyze_document input: {doc}")
        # Call detect through the mock to track the call
        mock.detect(doc["content"]["body"])
        result = {
            **doc,
            "metadata": {
                **(doc.get("metadata", {})),
                "pii_analysis": {"found_types": [], "match_count": 0, "matches_by_type": {}},
            },
        }
        logger.debug(f"PIIDetector.analyze_document output: {result}")
        return result

    mock.detect = MagicMock(side_effect=detect_with_logging)
    mock.analyze_document = MagicMock(side_effect=analyze_with_logging)
    return mock


def create_document_processor_mock():
    """Create mock document processor with logging."""
    mock = MagicMock()

    def deduplicate_with_logging(x):
        logger.debug(f"DocumentProcessor.deduplicate_documents input: {x}")
        result = x
        logger.debug(f"DocumentProcessor.deduplicate_documents output: {result}")
        return result

    def batch_with_logging(docs, size):
        logger.debug(f"DocumentProcessor.batch_documents input: {docs}, size: {size}")
        result = [[doc] for doc in docs]
        logger.debug(f"DocumentProcessor.batch_documents output: {result}")
        return result

    mock.deduplicate_documents = MagicMock(side_effect=deduplicate_with_logging)
    mock.deduplicate = MagicMock(side_effect=deduplicate_with_logging)  # Alias for test
    mock.batch_documents = MagicMock(side_effect=batch_with_logging)
    return mock


def create_document_summarizer_mock():
    """Create mock document summarizer with logging."""
    mock = MagicMock()

    def process_with_logging(docs, config=None):
        max_length = config.get("max_length") if config else None
        logger.debug(
            f"DocumentSummarizer.process_documents input: {docs}, max_length: {max_length}"
        )
        # Also call summarize to satisfy test
        mock.summarize(max_length=max_length)
        result = [{**doc, "processed": True, "pipeline_version": "1.0.0"} for doc in docs]
        logger.debug(f"DocumentSummarizer.process_documents output: {result}")
        return result

    mock.process_documents = MagicMock(side_effect=process_with_logging)
    mock.summarize = MagicMock()
    return mock


def create_topic_clusterer_mock():
    """Create mock topic clusterer with logging."""
    mock = MagicMock()

    def cluster_docs_with_logging(docs, config=None):
        n_clusters = config.get("n_clusters") if config else None
        logger.debug(f"TopicClusterer.cluster_documents input: {docs}, n_clusters: {n_clusters}")
        # Also call cluster to satisfy test
        mock.cluster(n_clusters=n_clusters)
        result = docs
        logger.debug(f"TopicClusterer.cluster_documents output: {result}")
        return result

    mock.cluster_documents = MagicMock(side_effect=cluster_docs_with_logging)
    mock.cluster = MagicMock()
    return mock


def create_vector_index_mock():
    """Create mock vector index with logging."""
    mock = MagicMock()

    def add_docs_with_logging(docs, **kwargs):
        logger.debug(f"VectorIndex.add_documents input: {docs}, kwargs: {kwargs}")
        # Ensure docs is a list
        if not isinstance(docs, list):
            docs = [docs]
        # Add IDs to documents and return them
        for i, doc in enumerate(docs):
            doc["id"] = f"doc_{i}"
        logger.debug(f"VectorIndex.add_documents processed docs: {docs}")
        return [doc["id"] for doc in docs]

    mock.add_documents = MagicMock(side_effect=add_docs_with_logging)
    return mock


def create_embedding_generator_mock():
    """Create mock embedding generator with logging."""
    mock = MagicMock()

    def process_docs_with_logging(docs):
        logger.info(f"EmbeddingGenerator.generate_embeddings input: {docs}")
        result = [{**doc, "processed": True, "pipeline_version": "1.0.0"} for doc in docs]
        logger.info(f"EmbeddingGenerator.generate_embeddings output: {result}")
        return result

    mock.generate_embeddings = MagicMock(side_effect=process_docs_with_logging)
    return mock


def create_notion_connector_mock():
    """Create mock Notion connector with test documents."""
    mock = MagicMock()
    test_docs = [
        {"content": {"body": "Test document 1", "metadata": {"title": "Doc 1"}}},
        {"content": {"body": "Test document 2", "metadata": {"title": "Doc 2"}}},
    ]
    mock.get_documents.return_value = test_docs
    return mock


@pytest.fixture(scope="function")
def pipeline_with_mocks(pipeline_state, request):
    """Pipeline instance with mocked components and state management."""
    # Create component patches
    component_classes = [
        "DocumentProcessor",
        "NotionConnector",
        "PIIDetector",
        "DocumentSummarizer",
        "EmbeddingGenerator",
        "TopicClusterer",
        "VectorIndex",
        "SearchOperations",
        "DocumentOperations",
    ]

    mock_creators = {
        "DocumentProcessor": create_document_processor_mock,
        "NotionConnector": create_notion_connector_mock,
        "PIIDetector": create_pii_detector_mock,
        "DocumentSummarizer": create_document_summarizer_mock,
        "EmbeddingGenerator": create_embedding_generator_mock,
        "TopicClusterer": create_topic_clusterer_mock,
        "VectorIndex": create_vector_index_mock,
        "SearchOperations": MagicMock,
        "DocumentOperations": MagicMock,
    }

    with patch.multiple(
        "src.pipeline.core", **{cls: DEFAULT for cls in component_classes}
    ) as mocks:
        # Configure component mocks
        for name, mock in mocks.items():
            mock.return_value = mock_creators[name]()

        yield mocks
