"""Tests for embedding generation utilities."""

import numpy as np
import pytest
from sentence_transformers import SentenceTransformer

from src.core.utils.ml.embeddings import EmbeddingGenerator
from src.core.utils.ml.exceptions import EmbeddingError, InputValidationError, ModelInitError


@pytest.fixture
def embedding_generator():
    """Create an embedding generator for testing."""
    return EmbeddingGenerator(model_name="all-MiniLM-L6-v2")


def test_initialization():
    """Test successful initialization."""
    generator = EmbeddingGenerator()
    assert isinstance(generator.model, SentenceTransformer)
    assert generator.batch_size == 32


def test_initialization_with_invalid_model():
    """Test initialization with invalid model name."""
    with pytest.raises(ModelInitError):
        EmbeddingGenerator(model_name="invalid-model-name")


def test_generate_embeddings(embedding_generator):
    """Test embedding generation with valid input."""
    texts = ["This is a test", "Another test sentence"]
    embeddings = embedding_generator.generate_embeddings(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, embedding_generator.get_embedding_dimension())
    assert not np.isnan(embeddings).any()


def test_generate_embeddings_empty_input(embedding_generator):
    """Test embedding generation with empty input."""
    with pytest.raises(InputValidationError, match="No texts provided"):
        embedding_generator.generate_embeddings([])


def test_generate_embeddings_invalid_input(embedding_generator):
    """Test embedding generation with invalid input types."""
    with pytest.raises(InputValidationError, match="All inputs must be strings"):
        embedding_generator.generate_embeddings([123, "test"])


def test_generate_embeddings_batch_size(embedding_generator):
    """Test embedding generation with custom batch size."""
    texts = ["Text " + str(i) for i in range(10)]
    embeddings = embedding_generator.generate_embeddings(texts, batch_size=5)
    assert embeddings.shape == (10, embedding_generator.get_embedding_dimension())


def test_get_embedding_dimension(embedding_generator):
    """Test getting embedding dimension."""
    dimension = embedding_generator.get_embedding_dimension()
    assert isinstance(dimension, int)
    assert dimension > 0


def test_context_manager():
    """Test using embedding generator as context manager."""
    texts = ["Test text"]
    with EmbeddingGenerator() as generator:
        embeddings = generator.generate_embeddings(texts)
        assert isinstance(embeddings, np.ndarray)
