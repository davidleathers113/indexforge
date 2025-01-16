"""Tests for the document processor component."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from src.models import ClusteringConfig
from src.pipeline.components.processor import DocumentProcessor
from src.pipeline.config.settings import PipelineConfig
from src.utils.summarizer.config.settings import SummarizerConfig


@pytest.fixture
def config():
    """Create a test configuration."""
    return PipelineConfig(export_dir='test_dir', batch_size=2, max_document_length=100, max_retries=2)


@pytest.fixture
def mock_base_processor():
    """Create a mock base document processor."""
    with patch('src.pipeline.components.processor.BaseDocProcessor') as mock:
        instance = mock.return_value
        instance.batch_documents.side_effect = lambda docs, batch_size: [docs]
        instance.deduplicate_documents.side_effect = lambda docs: docs
        instance.logger = logging.getLogger(__name__)
        yield instance


@pytest.fixture
def mock_pii_detector():
    """Create a mock PII detector."""
    with patch('src.pipeline.components.processor.PIIDetector') as mock:
        instance = mock.return_value
        instance.analyze_document.side_effect = lambda x: x
        yield instance


@pytest.fixture
def mock_summarizer():
    """Create a mock summarizer."""
    with patch('src.pipeline.components.processor.SummarizerProcessor') as mock:
        instance = mock.return_value
        instance.process_documents.side_effect = lambda docs, _: docs
        yield instance


@pytest.fixture
def mock_embedding_generator():
    """Create a mock embedding generator."""
    with patch('src.pipeline.components.processor.EmbeddingGenerator') as mock:
        instance = mock.return_value
        instance.generate_embeddings.side_effect = lambda docs: docs
        yield instance


@pytest.fixture
def mock_topic_clusterer():
    """Create a mock topic clusterer."""
    with patch('src.pipeline.components.processor.TopicClusterer') as mock:
        instance = mock.return_value
        instance.cluster_documents.side_effect = lambda docs, _: docs
        yield instance


@pytest.fixture
def processor(config, mock_base_processor, mock_pii_detector, mock_summarizer, mock_embedding_generator, mock_topic_clusterer):
    """Create a test processor."""
    return DocumentProcessor(config=config)


def test_processor_initialization(config, mock_base_processor, mock_pii_detector, mock_summarizer, mock_embedding_generator, mock_topic_clusterer):
    """Test processor initialization."""
    processor = DocumentProcessor(config=config)
    assert processor.config == config
    assert isinstance(processor.doc_processor, MagicMock)
    assert isinstance(processor.pii_detector, MagicMock)
    assert isinstance(processor.summarizer, MagicMock)
    assert isinstance(processor.embedding_generator, MagicMock)
    assert isinstance(processor.topic_clusterer, MagicMock)


def test_processor_process_empty(processor):
    """Test processing with no documents."""
    result = processor.process([])
    assert result == []


def test_processor_process_deduplication(processor, mock_base_processor, mock_embedding_generator):
    """Test document deduplication."""
    docs = [{'id': '1', 'content': {'body': 'test1'}}, {'id': '2', 'content': {'body': 'test2'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    mock_base_processor.deduplicate_documents.side_effect = lambda docs: [docs[0]]
    mock_embedding_generator.generate_embeddings.side_effect = lambda docs: docs
    result = processor.process(docs, deduplicate=True)
    assert len(result) == 1
    assert result[0]['id'] == '1'
    mock_base_processor.deduplicate_documents.assert_called_once_with(docs)


def test_processor_process_pii_detection(processor, mock_pii_detector, mock_base_processor):
    """Test PII detection."""
    docs = [{'id': '1', 'content': {'body': 'test'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    processor.process(docs, detect_pii=True)
    mock_pii_detector.analyze_document.assert_called_once_with(docs[0])


def test_processor_process_summarization(processor, mock_summarizer, mock_base_processor):
    """Test document summarization."""
    docs = [{'id': '1', 'content': {'body': 'test'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    summary_config = SummarizerConfig(model_name='test-model')
    processor.process(docs, summary_config=summary_config)
    mock_summarizer.process_documents.assert_called_once_with(docs, summary_config)


def test_processor_process_embedding_generation(processor, mock_embedding_generator, mock_base_processor):
    """Test embedding generation."""
    docs = [{'content': {'body': 'test'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    processor.process(docs)
    mock_embedding_generator.generate_embeddings.assert_called_once_with(docs)


def test_processor_process_topic_clustering(processor, mock_topic_clusterer, mock_base_processor):
    """Test topic clustering."""
    docs = [{'id': '1', 'content': {'body': 'test'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    cluster_config = ClusteringConfig()
    processor.process(docs, cluster_config=cluster_config)
    mock_topic_clusterer.cluster_documents.assert_called_once_with(docs, cluster_config)


def test_processor_document_length_truncation(processor, mock_base_processor):
    """Test document length truncation."""
    docs = [{'content': {'body': 'x' * 200}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    result = processor.process(docs)
    assert len(result[0]['content']['body']) == processor.config.max_document_length


def test_processor_embedding_generation_retries(processor, mock_embedding_generator, mock_base_processor):
    """Test embedding generation retries on failure."""
    docs = [{'content': {'body': 'test'}}]
    mock_base_processor.batch_documents.side_effect = lambda docs, _: [docs]
    mock_embedding_generator.generate_embeddings.side_effect = [Exception('First attempt'), docs]
    result = processor.process(docs)
    assert len(result) == 1
    assert mock_embedding_generator.generate_embeddings.call_count == 2


def test_processor_cleanup(processor, mock_summarizer, mock_topic_clusterer):
    """Test processor cleanup."""
    processor.cleanup()
    mock_summarizer.cleanup.assert_called_once()
    mock_topic_clusterer.cleanup.assert_called_once()