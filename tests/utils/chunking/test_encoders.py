"""Tests for token encoder implementations and factory.

This module contains integration tests for the token encoder factory and its
implementations, including caching behavior, fallback mechanisms, and error handling.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.utils.chunking.strategies.encoders import (
    TIKTOKEN_AVAILABLE,
    BasicEncoder,
    TiktokenEncoder,
    TokenEncoder,
    TokenEncoderFactory,
)


@pytest.fixture
def factory():
    """Fixture providing a clean encoder factory instance."""
    return TokenEncoderFactory()


class TestTokenEncoderFactory:
    """Tests for the TokenEncoderFactory class."""

    def test_encoder_caching(self, factory):
        """Test that encoders are properly cached."""
        encoder1 = factory.get_encoder("gpt-3.5-turbo")
        encoder2 = factory.get_encoder("gpt-3.5-turbo")
        # Should return the same instance
        assert encoder1 is encoder2

    def test_different_models_different_encoders(self, factory):
        """Test that different models get different encoders."""
        encoder1 = factory.get_encoder("gpt-3.5-turbo")
        encoder2 = factory.get_encoder("gpt-4")
        # Should be different instances
        assert encoder1 is not encoder2

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_tiktoken_encoder_creation(self, factory):
        """Test creation of tiktoken encoder when available."""
        encoder = factory.get_encoder("gpt-3.5-turbo")
        assert isinstance(encoder, TiktokenEncoder)

    @pytest.mark.skipif(TIKTOKEN_AVAILABLE, reason="tiktoken is available")
    def test_fallback_to_basic_encoder(self, factory):
        """Test fallback to basic encoder when tiktoken is not available."""
        encoder = factory.get_encoder("gpt-3.5-turbo")
        assert isinstance(encoder, BasicEncoder)

    def test_none_model_name(self, factory):
        """Test behavior with None model name."""
        encoder = factory.get_encoder(None)
        assert encoder is not None
        # Should still be able to encode/decode
        text = "Test text"
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)
        assert decoded.strip() == text.strip()

    def test_invalid_model_handling(self, factory):
        """Test handling of invalid model names."""
        with pytest.warns(UserWarning):
            encoder = factory.get_encoder("nonexistent-model")
            assert encoder is not None  # Should still return a working encoder


@pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
class TestTiktokenEncoder:
    """Tests for the TiktokenEncoder implementation."""

    def test_encoding_decoding(self):
        """Test basic encoding and decoding functionality."""
        encoder = TiktokenEncoder("gpt-3.5-turbo")
        text = "Hello, world! 🌟"
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)
        assert decoded == text

    def test_model_fallback(self):
        """Test fallback to base encoding for unknown models."""
        with pytest.warns(UserWarning):
            encoder = TiktokenEncoder("unknown-model")
            assert encoder.encoding is not None

    def test_special_tokens(self):
        """Test handling of special tokens and characters."""
        encoder = TiktokenEncoder()
        special_text = "Testing 🌟 emoji and\nnewlines\tand tabs"
        tokens = encoder.encode(special_text)
        decoded = encoder.decode(tokens)
        assert decoded == special_text

    @patch("tiktoken.encoding_for_model")
    def test_initialization_error(self, mock_encoding):
        """Test handling of initialization errors."""
        mock_encoding.side_effect = KeyError("Model not found")
        with pytest.warns(UserWarning):
            encoder = TiktokenEncoder("gpt-3.5-turbo")
            assert encoder.encoding is not None


class TestBasicEncoder:
    """Tests for the BasicEncoder implementation."""

    def test_basic_encoding_decoding(self):
        """Test basic word-based encoding and decoding."""
        encoder = BasicEncoder()
        text = "Simple test text"
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)
        assert decoded.strip() == text.strip()

    def test_empty_text(self):
        """Test handling of empty text."""
        encoder = BasicEncoder()
        assert encoder.encode("") == []
        assert encoder.decode([]) == ""

    def test_whitespace_preservation(self):
        """Test preservation of whitespace in basic encoding."""
        encoder = BasicEncoder()
        text = "Word1   Word2\tWord3\nWord4"
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)
        # Should preserve general structure while normalizing whitespace
        assert " ".join(decoded.split()) == " ".join(text.split())

    def test_out_of_bounds_indices(self):
        """Test handling of out-of-bounds token indices."""
        encoder = BasicEncoder()
        text = "Test text"
        tokens = encoder.encode(text)
        # Add some invalid indices
        invalid_tokens = tokens + [100, 200, -1]
        # Should not raise error and should ignore invalid indices
        decoded = encoder.decode(invalid_tokens)
        assert decoded.strip() == text.strip()


@pytest.mark.integration
class TestEncoderIntegration:
    """Integration tests for encoder system."""

    def test_factory_encoder_compatibility(self, factory):
        """Test compatibility between factory and encoders."""
        text = "Integration test text with special chars: 🌟 and numbers 12345"
        encoder = factory.get_encoder()
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)
        assert decoded.strip() == text.strip()

    def test_cross_encoder_token_handling(self, factory):
        """Test handling of tokens between different encoder instances."""
        text = "Test text for cross-encoder compatibility"
        encoder1 = factory.get_encoder("gpt-3.5-turbo")
        encoder2 = factory.get_encoder("gpt-4")

        # Each encoder should handle its own tokens correctly
        tokens1 = encoder1.encode(text)
        tokens2 = encoder2.encode(text)

        assert encoder1.decode(tokens1).strip() == text.strip()
        assert encoder2.decode(tokens2).strip() == text.strip()

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_tiktoken_error_recovery(self, factory):
        """Test recovery from tiktoken errors."""
        with patch("tiktoken.encoding_for_model") as mock_encoding:
            # Simulate temporary failure
            mock_encoding.side_effect = [Exception("Temporary error"), None]

            # Should fall back to basic encoder
            encoder = factory.get_encoder("gpt-3.5-turbo")
            assert encoder is not None

            # Basic functionality should still work
            text = "Test error recovery"
            tokens = encoder.encode(text)
            decoded = encoder.decode(tokens)
            assert decoded.strip() == text.strip()
