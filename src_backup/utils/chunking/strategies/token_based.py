"""Token-based text chunking strategy.

This module implements text chunking based on token counts using tiktoken.
"""

import logging

from .base import ChunkingStrategy, ChunkValidator
from .encoders import TokenEncoder, TokenEncoderFactory


logger = logging.getLogger(__name__)


class TokenBasedChunking(ChunkingStrategy):
    """Strategy for chunking text based on token counts."""

    def __init__(
        self, encoder_factory: TokenEncoderFactory, validator: ChunkValidator | None = None
    ):
        """Initialize token-based chunking.

        Args:
            encoder_factory: Factory for creating token encoders
            validator: Optional validator for chunking parameters
        """
        super().__init__(validator)
        self.encoder_factory = encoder_factory
        self._encoder = None

    def _ensure_encoder(self, model_name: str | None = None) -> TokenEncoder:
        """Ensure encoder is initialized.

        Args:
            model_name: Optional model name for encoder

        Returns:
            Initialized token encoder

        Raises:
            ImportError: If tokenization is not available
        """
        if not self._encoder:
            self._encoder = self.encoder_factory.get_encoder(model_name)
        return self._encoder

    def chunk(
        self, text: str, chunk_size: int, overlap: int = 0, model_name: str | None = None
    ) -> list[str]:
        """Split text into chunks based on token count.

        Args:
            text: Text to split into chunks
            chunk_size: Number of tokens per chunk
            overlap: Number of overlapping tokens between chunks
            model_name: Optional model name for tokenization

        Returns:
            List of text chunks

        Raises:
            ValueError: If chunking parameters are invalid
            ImportError: If tokenization is not available
        """
        if not text:
            return []

        self.validate_params(chunk_size, overlap)

        try:
            encoder = self._ensure_encoder(model_name)
            tokens = encoder.encode(text)
            chunks = []

            i = 0
            while i < len(tokens):
                # Get chunk of tokens
                chunk_end = min(i + chunk_size, len(tokens))
                chunk = tokens[i:chunk_end]

                # Convert back to text
                chunk_text = encoder.decode(chunk)
                if chunk_text.strip():  # Only add non-empty chunks
                    chunks.append(chunk_text)

                # Move forward by chunk_size - overlap
                i += max(1, chunk_size - overlap)

                # Safety check for infinite loops
                if i >= len(tokens) or (chunks and i <= len(encoder.encode(chunks[-1]))):
                    break

            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk text: {e!s}")
            raise ValueError(f"Token-based chunking failed: {e!s}") from e
