"""Text processing utilities.

This module provides core text processing functionality including cleaning,
normalization, and basic text manipulation operations.
"""

import re
from typing import List, Tuple


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing characters.

    Args:
        text: Text to clean

    Returns:
        Cleaned text with normalized whitespace and characters

    Raises:
        ValueError: If input text is None or empty
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("–", "-").replace("—", "-")

    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using common sentence boundaries.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences

    Raises:
        ValueError: If input text is None or empty
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    # Basic sentence splitting pattern
    pattern = r"(?<=[.!?])\s+"

    # Split and clean sentences
    sentences = [s.strip() for s in re.split(pattern, text) if s.strip()]

    return sentences


def find_text_boundaries(
    text: str, pattern: str, window_size: int = 100
) -> List[Tuple[int, int, float]]:
    """Find text boundaries around pattern matches with confidence scores.

    Args:
        text: Text to search in
        pattern: Pattern to search for
        window_size: Size of context window around matches

    Returns:
        List of tuples containing (start_pos, end_pos, confidence)

    Raises:
        ValueError: If input text or pattern is invalid
    """
    if not text or not pattern:
        raise ValueError("Text and pattern must not be empty")
    if window_size < 0:
        raise ValueError("Window size must be non-negative")

    boundaries = []
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    for match in matches:
        start_pos = max(0, match.start() - window_size)
        end_pos = min(len(text), match.end() + window_size)

        # Calculate confidence based on match quality
        match_len = match.end() - match.start()
        context_size = end_pos - start_pos
        confidence = min(1.0, match_len / context_size + 0.5)

        boundaries.append((start_pos, end_pos, confidence))

    return boundaries
