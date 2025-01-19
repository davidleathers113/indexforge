"""Tests for the embedding service."""

from unittest.mock import patch

import numpy as np
import pytest

from src.core import Chunk
from src.ml.embeddings.errors import ValidationError
from src.ml.embeddings.service import EmbeddingService
from src.ml.processing.models.service import ServiceNotInitializedError


async def test_service_initialization(embedding_service: EmbeddingService) -> None:
    """Test service initialization."""
    assert embedding_service.state.value == "running"
    assert embedding_service._generator is not None


async def test_validate_valid_chunk(
    embedding_service: EmbeddingService, valid_chunk: Chunk
) -> None:
    """Test validation of a valid chunk."""
    errors = embedding_service.validate_chunk(valid_chunk)
    assert not errors


async def test_validate_invalid_chunk(
    embedding_service: EmbeddingService, invalid_chunk: Chunk
) -> None:
    """Test validation of an invalid chunk."""
    errors = embedding_service.validate_chunk(invalid_chunk)
    assert errors
    assert any("empty" in error.lower() for error in errors)


@pytest.mark.parametrize(
    "content,expected_error",
    [
        ("", "empty"),
        ("a", "fewer than"),
        ("a" * (1024 * 1024 + 1), "maximum"),
    ],
)
async def test_validation_edge_cases(
    embedding_service: EmbeddingService, content: str, expected_error: str
) -> None:
    """Test validation with various edge cases."""
    chunk = Chunk(id="test", content=content, metadata={})
    errors = embedding_service.validate_chunk(chunk)
    assert any(expected_error in error.lower() for error in errors)


async def test_embed_chunk_success(embedding_service: EmbeddingService, valid_chunk: Chunk) -> None:
    """Test successful chunk embedding."""
    with patch.object(
        embedding_service._generator, "generate_embeddings", return_value=np.array([[1.0, 2.0]])
    ):
        embedding = embedding_service.embed_chunk(valid_chunk)
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (2,)


async def test_embed_chunk_validation_failure(
    embedding_service: EmbeddingService, invalid_chunk: Chunk
) -> None:
    """Test chunk embedding with validation failure."""
    with pytest.raises(ValueError) as exc_info:
        await embedding_service.embed_chunk(invalid_chunk)
    assert "empty" in str(exc_info.value).lower()


async def test_embed_chunks_batch(embedding_service: EmbeddingService, valid_chunk: Chunk) -> None:
    """Test batch chunk embedding."""
    chunks = [valid_chunk, valid_chunk]  # Use same chunk twice for testing
    mock_embeddings = np.array([[1.0, 2.0], [3.0, 4.0]])

    with patch.object(
        embedding_service._generator, "generate_embeddings", return_value=mock_embeddings
    ):
        embeddings = embedding_service.embed_chunks(chunks)
        assert len(embeddings) == 2
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape == (2,) for emb in embeddings)


async def test_service_cleanup(embedding_service: EmbeddingService) -> None:
    """Test service cleanup."""
    await embedding_service.cleanup()
    assert embedding_service.state.value == "stopped"
    assert embedding_service._generator is None


async def test_operations_after_cleanup(embedding_service: EmbeddingService) -> None:
    """Test operations after service cleanup."""
    await embedding_service.cleanup()
    with pytest.raises(ServiceNotInitializedError):
        await embedding_service.embed_chunk(Chunk(id="test", content="test", metadata={}))
