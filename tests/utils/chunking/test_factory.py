"""Tests for chunking factory and configuration.

This module contains tests for the chunking factory, including configuration
validation, strategy creation, caching behavior, and error handling.
"""

from enum import auto

import pytest

from src.utils.chunking.factory import ChunkingConfig, ChunkingFactory, ChunkingMethod
from src.utils.chunking.strategies.base import ChunkValidator
from src.utils.chunking.strategies.char_based import CharacterBasedChunking
from src.utils.chunking.strategies.token_based import TokenBasedChunking
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
def factory():
    """Fixture providing a clean factory instance."""
    return ChunkingFactory()


@pytest.fixture
def validator():
    """Fixture providing a test validator."""
    return TestValidator()


class TestChunkingConfig:
    """Tests for chunking configuration."""

    def test_valid_config(self):
        """Test valid configuration creation."""
        config = ChunkingConfig(method=ChunkingMethod.CHARACTER, chunk_size=100, overlap=20)
        assert config.chunk_size == 100
        assert config.overlap == 20
        assert config.respect_boundaries is True

    def test_invalid_chunk_size(self):
        """Test validation of invalid chunk size."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            ChunkingConfig(method=ChunkingMethod.WORD, chunk_size=0)

    def test_invalid_overlap(self):
        """Test validation of invalid overlap."""
        with pytest.raises(ValueError, match="Overlap must be non-negative"):
            ChunkingConfig(method=ChunkingMethod.CHARACTER, chunk_size=100, overlap=-1)

        with pytest.raises(ValueError, match="Overlap must be less than chunk size"):
            ChunkingConfig(method=ChunkingMethod.CHARACTER, chunk_size=100, overlap=100)

    def test_token_config_warning(self, caplog):
        """Test warning for token config without model."""
        config = ChunkingConfig(method=ChunkingMethod.TOKEN, chunk_size=100)
        assert "No model specified for token-based chunking" in caplog.text
        assert config.model_name is None  # Verify default value


class TestChunkingFactory:
    """Tests for chunking factory functionality."""

    def test_strategy_creation(self, factory):
        """Test creation of different strategy types."""
        configs = [
            (ChunkingMethod.CHARACTER, CharacterBasedChunking),
            (ChunkingMethod.WORD, WordBasedChunking),
            (ChunkingMethod.TOKEN, TokenBasedChunking),
        ]

        for method, expected_class in configs:
            config = ChunkingConfig(method=method, chunk_size=100)
            strategy = factory.get_strategy(config)
            assert isinstance(strategy, expected_class)

    def test_strategy_caching(self, factory):
        """Test that strategies are properly cached."""
        config = ChunkingConfig(method=ChunkingMethod.CHARACTER, chunk_size=100)

        strategy1 = factory.get_strategy(config)
        strategy2 = factory.get_strategy(config)
        assert strategy1 is strategy2  # Same instance

        # Different config should yield different instance
        config2 = ChunkingConfig(
            method=ChunkingMethod.CHARACTER, chunk_size=100, respect_boundaries=False
        )
        strategy3 = factory.get_strategy(config2)
        assert strategy1 is not strategy3

    def test_cache_clearing(self, factory):
        """Test cache clearing functionality."""
        config = ChunkingConfig(method=ChunkingMethod.WORD, chunk_size=100)

        strategy1 = factory.get_strategy(config)
        factory.clear_cache()
        strategy2 = factory.get_strategy(config)
        assert strategy1 is not strategy2

    def test_context_manager(self):
        """Test context manager behavior."""
        config = ChunkingConfig(method=ChunkingMethod.CHARACTER, chunk_size=100)

        with ChunkingFactory() as factory:
            strategy = factory.get_strategy(config)
            assert strategy is factory.get_strategy(config)

        # New factory should create new instance
        with ChunkingFactory() as factory2:
            assert factory2.get_strategy(config) is not strategy

    def test_chunking_convenience(self, factory):
        """Test convenience chunking method."""
        config = ChunkingConfig(method=ChunkingMethod.WORD, chunk_size=2, overlap=0)

        text = "one two three four"
        chunks = factory.chunk_text(text, config)
        assert len(chunks) == 2
        assert "one two" in chunks[0]
        assert "three four" in chunks[1]

    def test_invalid_method(self, factory):
        """Test handling of invalid chunking method."""

        class InvalidMethod(ChunkingMethod):
            INVALID = auto()

        config = ChunkingConfig(method=InvalidMethod.INVALID, chunk_size=100)

        with pytest.raises(ValueError, match="Unknown chunking method"):
            factory.get_strategy(config)

    def test_validator_propagation(self, factory, validator):
        """Test that validator is properly propagated."""
        config = ChunkingConfig(
            method=ChunkingMethod.CHARACTER, chunk_size=100, validator=validator
        )

        strategy = factory.get_strategy(config)
        assert strategy.validator is validator

    @pytest.mark.parametrize("method", list(ChunkingMethod))
    def test_boundary_respect(self, factory, method):
        """Test boundary respect setting for all methods."""
        config = ChunkingConfig(method=method, chunk_size=100, respect_boundaries=False)

        strategy = factory.get_strategy(config)
        if method == ChunkingMethod.CHARACTER:
            assert not strategy.respect_boundaries
        elif method == ChunkingMethod.WORD:
            assert not strategy.respect_sentences
        # TOKEN method doesn't use boundary respect
