"""Word-based text chunking strategy.

This module implements text chunking based on word counts, with support for
sentence boundary awareness and proper handling of punctuation and whitespace.
"""

import logging
import re

from .base import ChunkingStrategy, ChunkValidator


logger = logging.getLogger(__name__)

# Regex for finding sentence boundaries (period, question mark, exclamation mark followed by space or end)
SENTENCE_BOUNDARY = re.compile(r"[.!?](?:\s+|$)")

# Regex for splitting text into words while preserving punctuation and spacing
WORD_PATTERN = re.compile(r"(\s+|[^\s\w]+|\w+)")


class WordBasedChunking(ChunkingStrategy):
    """Strategy for chunking text based on word count.

    This strategy splits text into chunks containing a specified number of words,
    with options for overlapping chunks. It preserves punctuation and spacing,
    and can optionally respect sentence boundaries to maintain context.
    """

    def __init__(self, validator: ChunkValidator | None = None, respect_sentences: bool = True):
        """Initialize word-based chunking.

        Args:
            validator: Optional validator for chunking parameters
            respect_sentences: Whether to avoid splitting sentences when possible
        """
        super().__init__(validator)
        self.respect_sentences = respect_sentences

    def _split_into_words(self, text: str) -> list[tuple[str, bool]]:
        """Split text into words while preserving punctuation and spacing.

        Args:
            text: Text to split into words

        Returns:
            List of tuples containing (token, is_word) pairs
        """
        tokens = []
        for match in WORD_PATTERN.finditer(text):
            token = match.group()
            # Consider a token a word if it contains word characters
            is_word = bool(re.search(r"\w", token))
            tokens.append((token, is_word))
        return tokens

    def _find_sentence_end(
        self, tokens: list[tuple[str, bool]], start_idx: int, target_idx: int
    ) -> int:
        """Find the nearest sentence boundary.

        Args:
            tokens: List of (token, is_word) pairs
            start_idx: Start index to search from
            target_idx: Target index to find boundary near

        Returns:
            Index of the nearest sentence boundary
        """
        if not self.respect_sentences:
            return target_idx

        # Build text segment to search
        text = ""
        curr_pos = 0
        pos_to_idx = {}  # Maps character positions to token indices

        for i in range(start_idx, min(len(tokens), target_idx + 20)):  # Look ahead a bit
            token = tokens[i][0]
            pos_to_idx[curr_pos] = i
            text += token
            curr_pos += len(token)

        # Find last sentence boundary before target
        matches = list(SENTENCE_BOUNDARY.finditer(text))
        if matches:
            # Find the last sentence boundary that doesn't exceed target
            for match in reversed(matches):
                end_pos = match.end()
                if end_pos in pos_to_idx:
                    boundary_idx = pos_to_idx[end_pos]
                    if boundary_idx <= target_idx:
                        return boundary_idx

        return target_idx

    def chunk(self, text: str, chunk_size: int, overlap: int = 0) -> list[str]:
        """Split text into chunks based on word count.

        Args:
            text: Text to split into chunks
            chunk_size: Number of words per chunk
            overlap: Number of overlapping words between chunks

        Returns:
            List of text chunks

        Raises:
            ValueError: If chunking parameters are invalid
        """
        if not text:
            return []

        self.validate_params(chunk_size, overlap)

        try:
            # Split text into words and other tokens
            tokens = self._split_into_words(text)
            if not tokens:
                return []

            chunks = []
            word_count = 0
            start_idx = 0

            while start_idx < len(tokens):
                # Count words until we reach chunk_size
                curr_idx = start_idx
                chunk_words = 0

                while curr_idx < len(tokens) and chunk_words < chunk_size:
                    if tokens[curr_idx][1]:  # If it's a word
                        chunk_words += 1
                    curr_idx += 1

                # Find appropriate end boundary
                end_idx = self._find_sentence_end(tokens, start_idx, curr_idx)

                # Build chunk text
                chunk = "".join(token for token, _ in tokens[start_idx:end_idx])
                if chunk.strip():  # Only add non-empty chunks
                    chunks.append(chunk.strip())

                # Calculate next start position
                if overlap > 0:
                    # Count back 'overlap' words from end
                    word_count = 0
                    new_start = end_idx - 1
                    while new_start > start_idx and word_count < overlap:
                        if tokens[new_start][1]:  # If it's a word
                            word_count += 1
                        new_start -= 1
                    start_idx = new_start + 1
                else:
                    start_idx = end_idx

                # Safety check for infinite loops
                if start_idx >= len(tokens) or (chunks and start_idx >= len(tokens)):
                    break

            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk text: {e!s}")
            raise ValueError(f"Word-based chunking failed: {e!s}") from e
