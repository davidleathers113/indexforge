"""Tests for ML service processors.

This module contains tests for processor implementations.
"""

import pytest
from sentence_transformers import SentenceTransformer
from spacy.language import Language

from src.core.models.chunks import Chunk
from src.services.ml.validation.parameters import EmbeddingParameters, ProcessingParameters
from src.services.ml.validation.processors import EmbeddingProcessor, SpacyProcessor


@pytest.fixture
def spacy_model(mocker):
    """Mock spaCy model."""
    model = mocker.Mock(spec=Language)
    doc = mocker.Mock()
    doc.text = "test text"
    doc.tokens = [mocker.Mock(text="test", lemma_="test", pos_="NOUN")]
    doc.ents = [mocker.Mock(text="test", label_="TEST")]
    model.return_value = doc
    return model


@pytest.fixture
def transformer_model(mocker):
    """Mock sentence transformer model."""
    model = mocker.Mock(spec=SentenceTransformer)
    model.encode.return_value = [0.1, 0.2, 0.3]
    return model


@pytest.fixture
def test_chunk():
    """Create test chunk."""
    return Chunk(id="test", text="test text", metadata={})


class TestSpacyProcessor:
    """Tests for SpacyProcessor."""

    def test_process_chunk(self, spacy_model, test_chunk):
        """Test processing single chunk."""
        params = ProcessingParameters()
        processor = SpacyProcessor(spacy_model, params)

        result = processor.process_chunk(test_chunk)

        assert "tokens" in result
        assert "lemmas" in result
        assert "pos_tags" in result
        assert "entities" in result
        spacy_model.assert_called_once_with("test text", disable=[])

    def test_process_chunks(self, spacy_model):
        """Test processing multiple chunks."""
        params = ProcessingParameters()
        processor = SpacyProcessor(spacy_model, params)
        chunks = [
            Chunk(id="1", text="text 1", metadata={}),
            Chunk(id="2", text="text 2", metadata={}),
        ]

        results = processor.process_chunks(chunks)

        assert len(results) == 2
        assert all("tokens" in r for r in results)
        assert spacy_model.call_count == 2


class TestEmbeddingProcessor:
    """Tests for EmbeddingProcessor."""

    def test_process_chunk(self, transformer_model, test_chunk):
        """Test generating embeddings for single chunk."""
        params = EmbeddingParameters()
        processor = EmbeddingProcessor(transformer_model, params)

        result = processor.process_chunk(test_chunk)

        assert "embedding" in result
        assert isinstance(result["embedding"], list)
        transformer_model.encode.assert_called_once_with("test text", normalize_embeddings=True)

    def test_process_chunks(self, transformer_model):
        """Test generating embeddings for multiple chunks."""
        params = EmbeddingParameters()
        processor = EmbeddingProcessor(transformer_model, params)
        chunks = [
            Chunk(id="1", text="text 1", metadata={}),
            Chunk(id="2", text="text 2", metadata={}),
        ]

        results = processor.process_chunks(chunks)

        assert len(results) == 2
        assert all("embedding" in r for r in results)
        transformer_model.encode.assert_called_once_with(
            ["text 1", "text 2"], normalize_embeddings=True
        )
