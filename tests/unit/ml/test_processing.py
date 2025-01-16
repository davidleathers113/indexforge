"""Unit tests for the ML package's chunk processing functionality."""

from unittest.mock import Mock, patch

import pytest

from src.core.models.chunks import Chunk, ProcessedChunk
from src.core.models.documents import DocumentStatus, ProcessingStep
from src.ml.processing import (
    SPACY_AVAILABLE,
    ChunkProcessor,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
    ServiceStateError,
)


@pytest.fixture
def settings():
    """Create mock settings for testing."""
    return Mock()


@pytest.fixture
def processor(settings):
    """Create a ChunkProcessor instance for testing."""
    return ChunkProcessor(settings)


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return Chunk(
        id="test-chunk-1",
        content="This is a test chunk about Apple Inc. and Microsoft Corporation.",
        metadata={"source": "test"},
    )


@pytest.fixture
def mock_nlp():
    """Create a mock spaCy NLP object."""
    mock = Mock()
    mock.tokenizer = Mock()

    # Mock document processing
    doc = Mock()
    doc.ents = [
        Mock(text="Apple Inc.", label_="ORG", start_char=23, end_char=32),
        Mock(text="Microsoft Corporation", label_="ORG", start_char=37, end_char=58),
    ]
    doc.__len__ = lambda: 10  # For sentiment calculation
    doc.sentiment = 0.5

    tokens = [Mock(text=word) for word in ["This", "is", "a", "test", "chunk"]]
    doc.__iter__ = lambda self: iter(tokens)

    mock.return_value = doc
    return mock


class TestChunkProcessor:
    """Test suite for ChunkProcessor class."""

    def test_initialization(self, processor):
        """Test processor initialization."""
        assert processor._state == ServiceState.CREATED
        assert processor._nlp is None
        assert processor._tokenizer is None

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not available")
    def test_initialize_success(self, processor):
        """Test successful initialization with spaCy."""
        processor.initialize()
        assert processor._state == ServiceState.RUNNING
        assert processor._nlp is not None
        assert processor._tokenizer is not None

    def test_initialize_no_spacy(self, processor):
        """Test initialization failure when spaCy is not available."""
        with patch("src.ml.processing.SPACY_AVAILABLE", False):
            with pytest.raises(ServiceInitializationError) as exc_info:
                processor.initialize()
            assert "spaCy is required" in str(exc_info.value)
            assert processor._state == ServiceState.ERROR

    def test_cleanup(self, processor):
        """Test cleanup functionality."""
        processor._nlp = Mock()
        processor._tokenizer = Mock()
        processor._state = ServiceState.RUNNING

        processor.cleanup()

        assert processor._nlp is None
        assert processor._tokenizer is None
        assert processor._state == ServiceState.STOPPED

    def test_validate_chunk_success(self, processor, sample_chunk):
        """Test successful chunk validation."""
        errors = processor.validate_chunk(sample_chunk)
        assert not errors

    def test_validate_chunk_invalid_content(self, processor):
        """Test validation with invalid chunk content."""
        chunk = Chunk(id="test", content="", metadata={})
        errors = processor.validate_chunk(chunk)
        assert len(errors) > 0
        assert any("empty" in error for error in errors)

    def test_validate_chunk_invalid_metadata(self, processor):
        """Test validation with invalid metadata."""
        chunk = Chunk(id="test", content="valid content", metadata="invalid")
        errors = processor.validate_chunk(chunk)
        assert len(errors) > 0
        assert any("metadata must be a dictionary" in error for error in errors)

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not available")
    def test_process_chunk_success(self, processor, sample_chunk, mock_nlp):
        """Test successful chunk processing."""
        with patch("spacy.load", return_value=mock_nlp):
            processor.initialize()
            result = processor.process_chunk(sample_chunk)

            assert isinstance(result, ProcessedChunk)
            assert result.id == sample_chunk.id
            assert result.content == sample_chunk.content
            assert result.metadata == sample_chunk.metadata
            assert len(result.tokens) > 0
            assert len(result.named_entities) == 2
            assert result.sentiment_score == 0.5
            assert result.topic_id is None

    def test_process_chunk_not_initialized(self, processor, sample_chunk):
        """Test processing when service is not initialized."""
        with pytest.raises(ServiceStateError):
            processor.process_chunk(sample_chunk)

    def test_process_chunks_batch(self, processor, sample_chunk, mock_nlp):
        """Test processing multiple chunks."""
        chunks = [sample_chunk, sample_chunk]

        with patch("spacy.load", return_value=mock_nlp):
            processor.initialize()
            results = processor.process_chunks(chunks)

            assert len(results) == 2
            assert all(isinstance(result, ProcessedChunk) for result in results)

    def test_get_processing_steps(self, processor):
        """Test retrieving processing steps."""
        steps = processor.get_processing_steps()

        assert len(steps) == 3
        assert all(isinstance(step, ProcessingStep) for step in steps)
        assert all(step.status == DocumentStatus.PROCESSED for step in steps)

        step_names = {step.step_name for step in steps}
        expected_names = {"tokenization", "ner", "sentiment"}
        assert step_names == expected_names
