"""Character-based text chunking strategy.

This module implements text chunking based on character counts, with support for
sentence and word boundary awareness to avoid splitting in the middle of words.
"""

import logging
import re
from typing import List

from .base import ChunkingStrategy, ChunkValidator

logger = logging.getLogger(__name__)

# Regex for finding sentence boundaries (period, question mark, exclamation mark followed by space)
SENTENCE_BOUNDARY = re.compile(r"[.!?]\s+")
# Regex for finding word boundaries (whitespace)
WORD_BOUNDARY = re.compile(r"\s+")


class CharacterBasedChunking(ChunkingStrategy):
    """Strategy for chunking text based on character count.

    This strategy splits text into chunks of specified character length, with options
    for overlapping chunks. It attempts to split at sentence boundaries when possible,
    falling back to word boundaries to avoid splitting words.
    """

    def __init__(self, validator: ChunkValidator | None = None, respect_boundaries: bool = True):
        """Initialize character-based chunking.

        Args:
            validator: Optional validator for chunking parameters
            respect_boundaries: Whether to respect sentence and word boundaries
        """
        super().__init__(validator)
        self.respect_boundaries = respect_boundaries

    def _find_boundary(self, text: str, target_pos: int, window: int = 100) -> int:
        """Find the nearest natural boundary to split text.

        Args:
            text: Text to analyze
            target_pos: Target position to find boundary near
            window: Window size to search for boundaries

        Returns:
            Position of the nearest boundary
        """
        if not self.respect_boundaries:
            return target_pos

        # Search window around target position
        start = max(0, target_pos - window)
        end = min(len(text), target_pos + window)
        search_text = text[start:end]

        # First try to find sentence boundary
        sentence_matches = list(SENTENCE_BOUNDARY.finditer(search_text))
        if sentence_matches:
            # Find closest sentence boundary
            closest_match = min(sentence_matches, key=lambda m: abs(m.end() + start - target_pos))
            return closest_match.end() + start

        # Fall back to word boundary
        word_matches = list(WORD_BOUNDARY.finditer(search_text))
        if word_matches:
            # Find closest word boundary
            closest_match = min(word_matches, key=lambda m: abs(m.end() + start - target_pos))
            return closest_match.end() + start

        # If no boundaries found, return original position
        return target_pos

    def chunk(self, text: str, chunk_size: int, overlap: int = 0) -> List[str]:
        """Split text into chunks based on character count.

        Args:
            text: Text to split into chunks
            chunk_size: Number of characters per chunk
            overlap: Number of overlapping characters between chunks

        Returns:
            List of text chunks

        Raises:
            ValueError: If chunking parameters are invalid
        """
        if not text:
            return []

        self.validate_params(chunk_size, overlap)

        try:
            chunks = []
            start = 0
            text_len = len(text)

            while start < text_len:
                # Calculate end position
                raw_end = min(start + chunk_size, text_len)

                # Find appropriate boundary
                end = self._find_boundary(text, raw_end)

                # Extract chunk
                chunk = text[start:end].strip()
                if chunk:  # Only add non-empty chunks
                    chunks.append(chunk)

                # Move start position forward
                start = max(start + 1, end - overlap)

                # Safety check for infinite loops
                if start >= text_len or (chunks and start >= len(chunks[-1])):
                    break

            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk text: {e!s}")
            raise ValueError(f"Character-based chunking failed: {e!s}") from e
