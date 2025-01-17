"""Token encoder implementations and factory.

This module provides token encoder implementations and a factory for creating them.
"""

import logging
from typing import Dict, Protocol

logger = logging.getLogger(__name__)

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, falling back to basic tokenization")


class TokenEncoder(Protocol):
    """Protocol for token encoders."""

    def encode(self, text: str) -> list[int]:
        """Encode text into tokens."""
        ...

    def decode(self, tokens: list[int]) -> str:
        """Decode tokens back into text."""
        ...


class TiktokenEncoder:
    """Token encoder using tiktoken."""

    def __init__(self, model_name: str | None = None):
        """Initialize tiktoken encoder.

        Args:
            model_name: Optional model name for encoding

        Raises:
            ImportError: If tiktoken is not available
        """
        if not TIKTOKEN_AVAILABLE:
            raise ImportError("tiktoken is required for TiktokenEncoder")

        self.model_name = model_name or "gpt-3.5-turbo"
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            logger.warning(f"Model {self.model_name} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        """Encode text into tokens.

        Args:
            text: Text to encode

        Returns:
            List of token IDs
        """
        return self.encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode tokens back into text.

        Args:
            tokens: List of token IDs

        Returns:
            Decoded text
        """
        return self.encoding.decode(tokens)


class BasicEncoder:
    """Simple word-based encoder for fallback."""

    def encode(self, text: str) -> list[int]:
        """Encode text into word indices.

        Args:
            text: Text to encode

        Returns:
            List of word indices
        """
        return [i for i, _ in enumerate(text.split())]

    def decode(self, tokens: list[int]) -> str:
        """Decode word indices back into text.

        Args:
            tokens: List of word indices

        Returns:
            Decoded text
        """
        # Store text during encode for use in decode
        if not hasattr(self, "_words"):
            return ""
        return " ".join(self._words[i] for i in tokens if i < len(self._words))


class TokenEncoderFactory:
    """Factory for creating token encoders."""

    def __init__(self):
        """Initialize the factory."""
        self._encoders: Dict[str | None, TokenEncoder] = {}

    def get_encoder(self, model_name: str | None = None) -> TokenEncoder:
        """Get or create a token encoder.

        Args:
            model_name: Optional model name for encoding

        Returns:
            Token encoder instance

        Raises:
            ValueError: If encoder creation fails
        """
        if model_name in self._encoders:
            return self._encoders[model_name]

        try:
            if TIKTOKEN_AVAILABLE:
                encoder = TiktokenEncoder(model_name)
            else:
                logger.warning("Using basic encoder as tiktoken is not available")
                encoder = BasicEncoder()

            self._encoders[model_name] = encoder
            return encoder

        except Exception as e:
            logger.error(f"Failed to create encoder: {e!s}")
            raise ValueError(f"Failed to create encoder: {e!s}") from e
