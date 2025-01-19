"""Performance benchmarks for text chunking strategies.

This module contains performance tests and benchmarks for measuring the efficiency
of different chunking strategies under various conditions.
"""

import statistics
import time
from typing import Any

import pytest

from src.utils.chunking.strategies.base import ChunkingStrategy, ChunkValidator
from src.utils.chunking.strategies.char_based import CharacterBasedChunking
from src.utils.chunking.strategies.token_based import TokenBasedChunking, TokenEncoderFactory
from src.utils.chunking.strategies.word_based import WordBasedChunking


# Test data for benchmarks
BENCHMARK_TEXTS = {
    "small": "word " * 100,  # ~500 chars
    "medium": "word " * 1000,  # ~5000 chars
    "large": "word " * 10000,  # ~50000 chars
    "mixed": f"{'word ' * 100}{'数字 ' * 100}{'λέξη ' * 100}",  # Mixed scripts
    "technical": "def function():\n" + "    x = 1\n" * 1000,  # Code-like content
}

CHUNK_SIZES = {
    "small": 100,
    "medium": 500,
    "large": 1000,
}


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


class BenchmarkResult:
    """Container for benchmark results."""

    def __init__(self):
        self.times: dict[str, float] = {}
        self.chunk_counts: dict[str, int] = {}
        self.memory_usage: dict[str, float] = {}

    def add_result(self, name: str, time_taken: float, chunk_count: int, memory_used: float):
        """Add a benchmark result."""
        self.times[name] = time_taken
        self.chunk_counts[name] = chunk_count
        self.memory_usage[name] = memory_used

    def get_stats(self) -> dict[str, Any]:
        """Get statistical summary of results."""
        return {
            "time_mean": statistics.mean(self.times.values()),
            "time_stdev": statistics.stdev(self.times.values()) if len(self.times) > 1 else 0,
            "chunk_count_mean": statistics.mean(self.chunk_counts.values()),
            "memory_mean": statistics.mean(self.memory_usage.values()),
        }


class PerformanceBase:
    """Base class for performance testing."""

    strategy_class: type[ChunkingStrategy] = None

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing strategy instance."""
        if not self.strategy_class:
            pytest.skip("Base test class")
        return self.strategy_class(validator=validator)

    def benchmark_chunking(
        self, strategy, text: str, chunk_size: int, overlap: int = 0, iterations: int = 5
    ) -> BenchmarkResult:
        """Run benchmark for chunking operation.

        Args:
            strategy: Chunking strategy to test
            text: Input text
            chunk_size: Size of chunks
            overlap: Overlap between chunks
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult with timing and resource usage data
        """
        result = BenchmarkResult()

        for i in range(iterations):
            # Measure time
            start_time = time.perf_counter()
            chunks = strategy.chunk(text, chunk_size, overlap)
            end_time = time.perf_counter()

            # Collect metrics
            time_taken = end_time - start_time
            chunk_count = len(chunks)
            memory_used = sum(len(chunk) for chunk in chunks)  # Approximate

            result.add_result(f"iter_{i}", time_taken, chunk_count, memory_used)

        return result

    @pytest.mark.benchmark
    def test_text_size_scaling(self, strategy):
        """Test how performance scales with text size."""
        results = {}

        for size, text in BENCHMARK_TEXTS.items():
            result = self.benchmark_chunking(strategy, text, chunk_size=CHUNK_SIZES["medium"])
            results[size] = result.get_stats()

        # Verify reasonable scaling
        assert results["large"]["time_mean"] < results["medium"]["time_mean"] * 15

    @pytest.mark.benchmark
    def test_chunk_size_impact(self, strategy):
        """Test impact of chunk size on performance."""
        results = {}
        text = BENCHMARK_TEXTS["medium"]

        for size_name, chunk_size in CHUNK_SIZES.items():
            result = self.benchmark_chunking(strategy, text, chunk_size=chunk_size)
            results[size_name] = result.get_stats()

        # Verify chunk size impact
        assert results["large"]["chunk_count_mean"] < results["small"]["chunk_count_mean"]

    @pytest.mark.benchmark
    def test_overlap_overhead(self, strategy):
        """Test overhead of overlap processing."""
        text = BENCHMARK_TEXTS["medium"]
        chunk_size = CHUNK_SIZES["medium"]

        no_overlap = self.benchmark_chunking(strategy, text, chunk_size=chunk_size, overlap=0)
        with_overlap = self.benchmark_chunking(
            strategy, text, chunk_size=chunk_size, overlap=chunk_size // 2
        )

        # Verify reasonable overlap overhead
        assert with_overlap.get_stats()["time_mean"] < no_overlap.get_stats()["time_mean"] * 2


class TestCharacterPerformance(PerformanceBase):
    """Performance tests for character-based chunking."""

    strategy_class = CharacterBasedChunking

    @pytest.mark.benchmark
    def test_boundary_impact(self, strategy):
        """Test performance impact of boundary respect."""
        text = BENCHMARK_TEXTS["medium"]

        # Test with and without boundary respect
        standard = self.benchmark_chunking(strategy, text, chunk_size=CHUNK_SIZES["medium"])
        no_boundaries = self.benchmark_chunking(
            CharacterBasedChunking(respect_boundaries=False), text, chunk_size=CHUNK_SIZES["medium"]
        )

        # Verify boundary checking overhead
        assert standard.get_stats()["time_mean"] < no_boundaries.get_stats()["time_mean"] * 1.5


class TestWordPerformance(PerformanceBase):
    """Performance tests for word-based chunking."""

    strategy_class = WordBasedChunking

    @pytest.mark.benchmark
    def test_sentence_respect_impact(self, strategy):
        """Test performance impact of sentence boundary respect."""
        text = BENCHMARK_TEXTS["medium"]

        # Test with and without sentence respect
        standard = self.benchmark_chunking(strategy, text, chunk_size=CHUNK_SIZES["medium"])
        no_sentences = self.benchmark_chunking(
            WordBasedChunking(respect_sentences=False), text, chunk_size=CHUNK_SIZES["medium"]
        )

        # Verify sentence checking overhead
        assert standard.get_stats()["time_mean"] < no_sentences.get_stats()["time_mean"] * 1.5


@pytest.mark.integration
class TestTokenPerformance(PerformanceBase):
    """Performance tests for token-based chunking."""

    strategy_class = TokenBasedChunking

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing token-based strategy instance."""
        return self.strategy_class(TokenEncoderFactory(), validator=validator)

    @pytest.mark.benchmark
    def test_encoder_caching(self, strategy):
        """Test performance impact of encoder caching."""
        text = BENCHMARK_TEXTS["medium"]

        # First run to warm up cache
        _ = self.benchmark_chunking(strategy, text, chunk_size=CHUNK_SIZES["medium"], iterations=1)

        # Subsequent run with warm cache
        cached = self.benchmark_chunking(strategy, text, chunk_size=CHUNK_SIZES["medium"])

        # Verify reasonable cache performance
        assert cached.get_stats()["time_mean"] < 1.0  # Should be fast with cache
