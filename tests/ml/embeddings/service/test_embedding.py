"""Tests for core embedding functionality."""

import pytest

from tests.ml.embeddings.builders import ChunkBuilder
from tests.ml.embeddings.fixtures import EmbeddingServiceFactory


class TestEmbeddingGeneration:
    """Test suite for embedding generation functionality."""

    @pytest.mark.asyncio
    async def test_embed_single_chunk(self) -> None:
        """Test embedding generation for a single chunk."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder().with_content("Test embedding generation").build()
        embedding = await service.embed_chunk(chunk)

        assert embedding is not None
        assert len(embedding) == 384  # Expected dimension for all-MiniLM-L6-v2
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_embed_multiple_chunks(self) -> None:
        """Test embedding generation for multiple chunks."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunks = [ChunkBuilder().with_content(f"Test content {i}").build() for i in range(3)]
        embeddings = await service.embed_chunks(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 384 for emb in embeddings)
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_embedding_consistency(self) -> None:
        """Test that same input produces consistent embeddings."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder().with_content("Test consistency").build()

        # Generate embeddings twice for same content
        embedding1 = await service.embed_chunk(chunk)
        embedding2 = await service.embed_chunk(chunk)

        # Should produce identical embeddings
        assert all(e1 == e2 for e1, e2 in zip(embedding1, embedding2))
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_embedding_normalization(self) -> None:
        """Test that embeddings are properly normalized."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunk = ChunkBuilder().with_content("Test normalization").build()
        embedding = await service.embed_chunk(chunk)

        # Values should be normalized (between -1 and 1)
        assert all(abs(x) <= 1.0 for x in embedding)
        await service.cleanup()


class TestEmbeddingBehavior:
    """Test suite for embedding behavior characteristics."""

    @pytest.mark.asyncio
    async def test_similar_content_similarity(self) -> None:
        """Test that similar content produces similar embeddings."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        # Create chunks with similar content
        chunk1 = ChunkBuilder().with_content("The quick brown fox").build()
        chunk2 = ChunkBuilder().with_content("A swift brown fox").build()
        chunk3 = ChunkBuilder().with_content("Completely different content").build()

        emb1 = await service.embed_chunk(chunk1)
        emb2 = await service.embed_chunk(chunk2)
        emb3 = await service.embed_chunk(chunk3)

        # Calculate cosine similarities
        sim12 = self._cosine_similarity(emb1, emb2)
        sim13 = self._cosine_similarity(emb1, emb3)

        # Similar content should have higher similarity
        assert sim12 > sim13
        await service.cleanup()

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (norm1 * norm2)

    @pytest.mark.asyncio
    async def test_batch_processing_equivalence(self) -> None:
        """Test that batch processing produces same results as individual processing."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        chunks = [ChunkBuilder().with_content(f"Test content {i}").build() for i in range(3)]

        # Process individually
        individual_embeddings = []
        for chunk in chunks:
            emb = await service.embed_chunk(chunk)
            individual_embeddings.append(emb)

        # Process as batch
        batch_embeddings = await service.embed_chunks(chunks)

        # Results should be identical
        for ind_emb, batch_emb in zip(individual_embeddings, batch_embeddings):
            assert all(i == b for i, b in zip(ind_emb, batch_emb))

        await service.cleanup()
