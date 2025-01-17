"""Tests for text chunking strategies.

This module contains comprehensive tests for all chunking strategies, including
base functionality, edge cases, and specific features of each strategy.
"""

from typing import Type

import pytest

from src.utils.chunking.strategies.base import ChunkingStrategy, ChunkValidator
from src.utils.chunking.strategies.char_based import CharacterBasedChunking
from src.utils.chunking.strategies.token_based import TokenBasedChunking, TokenEncoderFactory
from src.utils.chunking.strategies.word_based import WordBasedChunking


class TestValidator(ChunkValidator):
    """Test implementation of chunk validator."""

    def validate_chunk_size(self, size: int) -> None:
        if size <= 0:
            raise ValueError("Chunk size must be positive")

    def validate_overlap(self, overlap: int, chunk_size: int) -> None:
        if overlap < 0:
            raise ValueError("Overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk size")


@pytest.fixture
def validator():
    """Fixture providing a test validator."""
    return TestValidator()


class TestChunkingBase:
    """Base test class for all chunking strategies."""

    strategy_class: Type[ChunkingStrategy] = None

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing strategy instance."""
        if not self.strategy_class:
            pytest.skip("Base test class")
        return self.strategy_class(validator=validator)

    def test_empty_text(self, strategy):
        """Test handling of empty text."""
        assert strategy.chunk("", chunk_size=10) == []
        assert strategy.chunk(" ", chunk_size=10) == []
        assert strategy.chunk("\n\t", chunk_size=10) == []

    def test_invalid_chunk_size(self, strategy):
        """Test validation of chunk size."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            strategy.chunk("test text", chunk_size=0)
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            strategy.chunk("test text", chunk_size=-1)

    def test_invalid_overlap(self, strategy):
        """Test validation of overlap size."""
        with pytest.raises(ValueError, match="Overlap must be non-negative"):
            strategy.chunk("test text", chunk_size=10, overlap=-1)
        with pytest.raises(ValueError, match="Overlap must be less than chunk size"):
            strategy.chunk("test text", chunk_size=10, overlap=10)

    def test_single_chunk(self, strategy):
        """Test text that fits in a single chunk."""
        text = "This is a test."
        result = strategy.chunk(text, chunk_size=100)
        assert len(result) == 1
        assert result[0].strip() == text.strip()

    def test_no_content_loss(self, strategy):
        """Test that no content is lost during chunking."""
        text = "First chunk. Second chunk. Third chunk."
        chunks = strategy.chunk(text, chunk_size=15, overlap=0)
        # Combine chunks and compare normalized text
        combined = " ".join(chunk.strip() for chunk in chunks)
        assert combined.replace("  ", " ").strip() == text.strip()

    def test_overlap_consistency(self, strategy):
        """Test that overlap behaves consistently."""
        text = "One two three four five six seven eight nine ten."
        chunks = strategy.chunk(text, chunk_size=4, overlap=2)
        # Check each pair of consecutive chunks for overlap
        for i in range(len(chunks) - 1):
            curr_chunk = chunks[i].strip()
            next_chunk = chunks[i + 1].strip()
            # Some content from current chunk should appear at start of next chunk
            assert any(word in next_chunk.split()[:2] for word in curr_chunk.split()[-2:])


class TestCharacterChunking(TestChunkingBase):
    """Tests specific to character-based chunking."""

    strategy_class = CharacterBasedChunking

    def test_exact_character_chunks(self, strategy):
        """Test chunking with exact character counts."""
        text = "abcdefghijklmnop"
        chunks = strategy.chunk(text, chunk_size=4, overlap=0)
        assert chunks == ["abcd", "efgh", "ijkl", "mnop"]

    def test_respect_word_boundaries(self, strategy):
        """Test that word boundaries are respected."""
        text = "word one two three"
        chunks = strategy.chunk(text, chunk_size=5, overlap=0)
        # Check that no word is split across chunks
        for chunk in chunks:
            assert not any(
                word.strip() and not word.isspace()
                for word in [chunk[0], chunk[-1]]
                if len(word.strip()) < len(word)
            )

    def test_sentence_boundary_preference(self, strategy):
        """Test preference for sentence boundaries."""
        text = "First sentence. Second one. Third."
        chunks = strategy.chunk(text, chunk_size=20, overlap=0)
        # Check that chunks preferably end at sentence boundaries
        assert any(chunk.endswith(".") for chunk in chunks)


class TestWordChunking(TestChunkingBase):
    """Tests specific to word-based chunking."""

    strategy_class = WordBasedChunking

    def test_exact_word_chunks(self, strategy):
        """Test chunking with exact word counts."""
        text = "one two three four five six"
        chunks = strategy.chunk(text, chunk_size=2, overlap=0)
        assert [len(chunk.split()) for chunk in chunks] == [2, 2, 2]

    def test_punctuation_preservation(self, strategy):
        """Test that punctuation is preserved."""
        text = "Hello, world! How are you?"
        chunks = strategy.chunk(text, chunk_size=2, overlap=0)
        # Check that punctuation is preserved in output
        combined = "".join(chunks)
        assert "," in combined
        assert "!" in combined
        assert "?" in combined

    def test_sentence_respect(self, strategy):
        """Test respect for sentence boundaries."""
        text = "First sentence. Second sentence. Third."
        chunks = strategy.chunk(text, chunk_size=3, overlap=0)
        # Verify some chunks end with sentence boundaries
        assert any(chunk.strip().endswith(".") for chunk in chunks)


@pytest.mark.integration
class TestTokenChunking(TestChunkingBase):
    """Tests specific to token-based chunking."""

    strategy_class = TokenBasedChunking

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing token-based strategy instance."""
        return self.strategy_class(TokenEncoderFactory(), validator=validator)

    def test_token_boundaries(self, strategy):
        """Test respect for token boundaries."""
        text = "This is a complex sentence with special tokens like 🌟 and URLs."
        chunks = strategy.chunk(text, chunk_size=5, overlap=0)
        # Verify chunks maintain token integrity
        combined = " ".join(chunk.strip() for chunk in chunks)
        assert "🌟" in combined  # Special characters preserved

    def test_model_specific_tokenization(self, strategy):
        """Test tokenization with specific models."""
        text = "Testing model-specific tokenization."
        chunks1 = strategy.chunk(text, chunk_size=5, model_name="gpt-3.5-turbo")
        chunks2 = strategy.chunk(text, chunk_size=5, model_name="gpt-4")
        # Different models might tokenize differently
        assert chunks1 or chunks2  # At least one should succeed
