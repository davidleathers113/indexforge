"""Edge case tests for text chunking strategies.

This module contains tests for complex scenarios and edge cases across all chunking
strategies, focusing on challenging inputs and boundary conditions.
"""

from typing import Type

import pytest

from src.utils.chunking.strategies.base import ChunkingStrategy, ChunkValidator
from src.utils.chunking.strategies.char_based import CharacterBasedChunking
from src.utils.chunking.strategies.token_based import TokenBasedChunking, TokenEncoderFactory
from src.utils.chunking.strategies.word_based import WordBasedChunking

# Test data constants
UNICODE_TEXT = "Hello 🌟 World! 汉字 αβγ \u0903 \u0904"
LARGE_TEXT = "word " * 10000  # 50000 characters
MIXED_SCRIPTS = "English हिन्दी 汉字 العربية Русский Ελληνικά"
NESTED_QUOTES = "He said \"She thought 'maybe' but wasn't sure\" and left."
TECHNICAL_TEXT = """
def example():
    # Complex indentation and symbols
    return [x for x in range(10) if x % 2 == 0]
"""
WHITESPACE_HEAVY = "\n\n\t  Multiple   \t\t  Spaces   \n\r\n"


@pytest.fixture
def validator():
    """Fixture providing a test validator."""
    return TestValidator()


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


class EdgeCaseBase:
    """Base class for edge case testing."""

    strategy_class: Type[ChunkingStrategy] = None

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing strategy instance."""
        if not self.strategy_class:
            pytest.skip("Base test class")
        return self.strategy_class(validator=validator)

    def test_unicode_handling(self, strategy):
        """Test handling of Unicode characters."""
        chunks = strategy.chunk(UNICODE_TEXT, chunk_size=5, overlap=2)
        # Verify no Unicode characters are corrupted
        combined = "".join(chunks)
        assert all(char in combined for char in "🌟汉字αβγ")

    def test_large_text(self, strategy):
        """Test handling of very large inputs."""
        chunks = strategy.chunk(LARGE_TEXT, chunk_size=1000, overlap=100)
        # Verify content preservation and chunk size constraints
        assert len("".join(chunks)) == len(LARGE_TEXT)
        assert all(len(chunk) <= 1000 for chunk in chunks)

    def test_mixed_scripts(self, strategy):
        """Test handling of mixed script systems."""
        chunks = strategy.chunk(MIXED_SCRIPTS, chunk_size=10, overlap=2)
        # Verify script mixing points are handled properly
        combined = "".join(chunks)
        for script in ["हिन्दी", "汉字", "العربية", "Русский", "Ελληνικά"]:
            assert script in combined

    def test_nested_punctuation(self, strategy):
        """Test handling of complex nested punctuation."""
        chunks = strategy.chunk(NESTED_QUOTES, chunk_size=20, overlap=5)
        # Verify quote nesting is preserved
        combined = "".join(chunks)
        assert combined.count('"') == NESTED_QUOTES.count('"')
        assert combined.count("'") == NESTED_QUOTES.count("'")

    def test_technical_content(self, strategy):
        """Test handling of technical content with special characters."""
        chunks = strategy.chunk(TECHNICAL_TEXT, chunk_size=20, overlap=5)
        # Verify indentation and symbols are preserved
        combined = "".join(chunks)
        assert "def example():" in combined
        assert "return [x for x" in combined

    def test_whitespace_handling(self, strategy):
        """Test handling of complex whitespace patterns."""
        chunks = strategy.chunk(WHITESPACE_HEAVY, chunk_size=10, overlap=2)
        # Verify whitespace handling
        combined = "".join(chunks)
        assert "\n\n" in combined
        assert "\t\t" in combined

    def test_zero_width_chars(self, strategy):
        """Test handling of zero-width characters."""
        text = "Hello\u200bWorld\u200c\u200d"  # Zero-width space, non-joiner, joiner
        chunks = strategy.chunk(text, chunk_size=5, overlap=1)
        combined = "".join(chunks)
        assert "\u200b" in combined
        assert "\u200c" in combined
        assert "\u200d" in combined

    def test_bidirectional_text(self, strategy):
        """Test handling of bidirectional text."""
        text = "Hello! مرحبا! שָׁלוֹם!"
        chunks = strategy.chunk(text, chunk_size=10, overlap=2)
        combined = "".join(chunks)
        assert "Hello" in combined
        assert "مرحبا" in combined
        assert "שָׁלוֹם" in combined


class TestCharacterEdgeCases(EdgeCaseBase):
    """Edge cases specific to character-based chunking."""

    strategy_class = CharacterBasedChunking

    def test_surrogate_pairs(self, strategy):
        """Test handling of surrogate pairs in UTF-16."""
        text = "😀😃😄"  # Each emoji is a surrogate pair
        chunks = strategy.chunk(text, chunk_size=2, overlap=0)
        combined = "".join(chunks)
        assert combined == text

    def test_combining_characters(self, strategy):
        """Test handling of combining characters."""
        text = "e\u0301"  # 'é' as 'e' + combining acute accent
        chunks = strategy.chunk(text, chunk_size=1, overlap=0)
        combined = "".join(chunks)
        assert combined == text


class TestWordEdgeCases(EdgeCaseBase):
    """Edge cases specific to word-based chunking."""

    strategy_class = WordBasedChunking

    def test_compound_words(self, strategy):
        """Test handling of compound words and hyphens."""
        text = "state-of-the-art high-quality well-being"
        chunks = strategy.chunk(text, chunk_size=2, overlap=0)
        combined = " ".join(chunk.strip() for chunk in chunks)
        assert "state-of-the-art" in combined

    def test_contractions(self, strategy):
        """Test handling of contractions."""
        text = "I'm can't wouldn't shouldn't"
        chunks = strategy.chunk(text, chunk_size=2, overlap=0)
        combined = " ".join(chunk.strip() for chunk in chunks)
        assert all(word in combined for word in ["I'm", "can't", "wouldn't", "shouldn't"])


@pytest.mark.integration
class TestTokenEdgeCases(EdgeCaseBase):
    """Edge cases specific to token-based chunking."""

    strategy_class = TokenBasedChunking

    @pytest.fixture
    def strategy(self, validator):
        """Fixture providing token-based strategy instance."""
        return self.strategy_class(TokenEncoderFactory(), validator=validator)

    def test_rare_tokens(self, strategy):
        """Test handling of rare and special tokens."""
        text = "var_123_xyz = @#$%^&* <special_token>"
        chunks = strategy.chunk(text, chunk_size=5, overlap=1)
        combined = " ".join(chunk.strip() for chunk in chunks)
        assert "var_123_xyz" in combined
        assert "@#$%^&*" in combined

    def test_code_snippets(self, strategy):
        """Test handling of code snippets."""
        text = 'print(f"Value: {x + y}")'
        chunks = strategy.chunk(text, chunk_size=5, overlap=1)
        combined = "".join(chunks)
        assert "print" in combined
        assert "{x + y}" in combined
