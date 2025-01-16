"""Test fixtures for chunk processor tests."""

import uuid
from typing import Any
from unittest.mock import Mock, patch

import pytest
from spacy.language import Language

from src.core.models.chunks import Chunk
from src.core.settings import Settings
from src.ml.processing.chunk import ChunkProcessor


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings()


@pytest.fixture
def mock_nlp() -> Mock:
    """Create a mock spaCy language model."""
    mock = Mock(spec=Language)
    mock.__call__ = Mock(return_value=Mock())  # Make the model callable
    return mock


@pytest.fixture
def mock_spacy(mock_nlp) -> None:
    """Mock spaCy module."""
    with patch("src.ml.processing.chunk.SPACY_AVAILABLE", True):
        with patch("src.ml.processing.chunk.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            yield mock_spacy


@pytest.fixture
def processor(settings: Settings, mock_spacy: Mock) -> ChunkProcessor:
    """Create an initialized chunk processor."""
    processor = ChunkProcessor(settings)
    processor.initialize()
    return processor


@pytest.fixture
def sample_chunk(processor: ChunkProcessor) -> Chunk:
    """Create a sample chunk for testing."""
    return Chunk(
        id=uuid.uuid4(),
        content="This is a test chunk with entities like John Smith and Google.",
        metadata={"source": "test", "language": "en"},
    )


@pytest.fixture
def sample_chunks(processor: ChunkProcessor) -> list[Chunk]:
    """Create multiple sample chunks for testing."""
    return [
        Chunk(
            id=uuid.uuid4(),
            content=f"Test chunk {i} with entity {name}.",
            metadata={"source": "test", "index": i},
        )
        for i, name in enumerate(["Alice", "Bob", "Charlie"])
    ]
