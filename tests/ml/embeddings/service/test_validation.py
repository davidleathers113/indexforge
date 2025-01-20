"""Tests for embedding service validation."""

import pytest

from tests.ml.embeddings.builders import ChunkBuilder
from tests.ml.embeddings.fixtures import EmbeddingServiceFactory


class TestInputValidation:
    """Test suite for input validation."""

    @pytest.mark.asyncio
    async def test_valid_chunk(self) -> None:
        """Test validation of valid chunk."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder.valid()
        errors = service.validate_chunk(chunk)
        assert not errors

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_chunk(self) -> None:
        """Test validation of invalid chunk."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder.invalid()
        errors = service.validate_chunk(chunk)
        assert errors
        assert any("empty" in error.lower() for error in errors)

        await service.cleanup()


class TestNumericValidation:
    """Test suite for numeric constraints."""

    @pytest.mark.asyncio
    async def test_embedding_numeric_constraints(self) -> None:
        """Test numeric constraints on embeddings."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder().with_content("Test numeric constraints").build()
        embedding = await service.embed_chunk(chunk)

        assert embedding is not None
        assert all(isinstance(x, float) for x in embedding)
        assert all(abs(x) <= 1.0 for x in embedding)  # Values should be normalized

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_batch_size_limits(self) -> None:
        """Test batch size limits for embedding generation."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunks = [ChunkBuilder().with_content(f"Test content {i}").build() for i in range(100)]

        embeddings = await service.embed_chunks(chunks)
        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 384 for emb in embeddings)

        await service.cleanup()


class TestContentValidation:
    """Test suite for content validation."""

    @pytest.mark.asyncio
    async def test_text_length_constraints(self) -> None:
        """Test text length constraints."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        # Test minimum length
        short_chunk = ChunkBuilder().with_content("a").build()
        with pytest.raises(ValueError) as exc_info:
            await service.embed_chunk(short_chunk)
        assert "length" in str(exc_info.value).lower()

        # Test maximum length
        long_chunk = ChunkBuilder().with_content("a" * 1000000).build()
        with pytest.raises(ValueError) as exc_info:
            await service.embed_chunk(long_chunk)
        assert "length" in str(exc_info.value).lower()

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_empty_batch_handling(self) -> None:
        """Test handling of empty batches."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        # Empty list should return empty result
        assert await service.embed_chunks([]) == []

        # None input should raise TypeError
        with pytest.raises(TypeError):
            await service.embed_chunks(None)  # type: ignore

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_content_types(self) -> None:
        """Test handling of invalid content types."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        invalid_chunks = [
            ChunkBuilder().with_content(None).build(),  # type: ignore
            ChunkBuilder().with_content(123).build(),  # type: ignore
            ChunkBuilder().with_content({"key": "value"}).build(),  # type: ignore
        ]

        for chunk in invalid_chunks:
            with pytest.raises((TypeError, ValueError)):
                await service.embed_chunk(chunk)

        await service.cleanup()
