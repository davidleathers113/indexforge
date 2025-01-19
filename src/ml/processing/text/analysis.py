"""Text analysis operations.

This module provides functions for analyzing text content, including
language detection, encoding detection, and content validation.
"""

import re
from typing import List, Optional, Tuple

try:
    import chardet

    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    import langdetect

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


def detect_language(text: str, min_confidence: float = 0.8) -> Tuple[Optional[str], float]:
    """Detect the language of text.

    Args:
        text: Text to analyze
        min_confidence: Minimum confidence threshold

    Returns:
        Tuple of (language code, confidence score)
        Returns (None, 0.0) if detection fails or confidence is too low

    Raises:
        ValueError: If text is empty
        RuntimeError: If langdetect is not available
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    if not LANGDETECT_AVAILABLE:
        raise RuntimeError("langdetect package is required for language detection")

    try:
        # Detect language
        result = langdetect.detect_langs(text)[0]
        lang = result.lang
        confidence = result.prob

        # Check confidence threshold
        if confidence < min_confidence:
            return None, 0.0

        return lang, confidence

    except Exception:
        return None, 0.0


def detect_encoding(text: bytes) -> Tuple[Optional[str], float]:
    """Detect the encoding of text data.

    Args:
        text: Bytes to analyze

    Returns:
        Tuple of (encoding name, confidence score)
        Returns (None, 0.0) if detection fails

    Raises:
        ValueError: If text is empty
        RuntimeError: If chardet is not available
    """
    if not text:
        raise ValueError("Input bytes cannot be None or empty")

    if not CHARDET_AVAILABLE:
        raise RuntimeError("chardet package is required for encoding detection")

    try:
        # Detect encoding
        result = chardet.detect(text)
        encoding = result["encoding"]
        confidence = result["confidence"]

        return encoding, confidence

    except Exception:
        return None, 0.0


def validate_content(text: str) -> List[str]:
    """Validate text content.

    Checks for common issues like:
    - Empty or whitespace-only content
    - Invalid characters
    - Excessive repetition
    - Unbalanced brackets/quotes

    Args:
        text: Text to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check for empty content
    if not text or not text.strip():
        errors.append("Text is empty or whitespace-only")
        return errors

    # Check for invalid characters
    invalid_chars = re.findall(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", text)
    if invalid_chars:
        errors.append(f"Text contains {len(invalid_chars)} invalid characters")

    # Check for excessive repetition
    if detect_repetition(text):
        errors.append("Text contains excessive repetition")

    # Check for unbalanced brackets/quotes
    if not check_balanced_delimiters(text):
        errors.append("Text contains unbalanced brackets or quotes")

    return errors


def check_format(text: str, format_type: str) -> bool:
    """Check if text matches expected format.

    Supported format types:
    - "sentence": Single sentence
    - "paragraph": Single paragraph
    - "list": Bullet or numbered list
    - "code": Code snippet

    Args:
        text: Text to check
        format_type: Expected format type

    Returns:
        True if text matches format, False otherwise

    Raises:
        ValueError: If format_type is invalid
    """
    if format_type not in {"sentence", "paragraph", "list", "code"}:
        raise ValueError(f"Invalid format type: {format_type}")

    if format_type == "sentence":
        # Check for single sentence
        sentences = re.split(r"[.!?]+", text.strip())
        return len([s for s in sentences if s.strip()]) == 1

    elif format_type == "paragraph":
        # Check for single paragraph (no double newlines)
        return "\n\n" not in text.strip()

    elif format_type == "list":
        # Check for bullet or numbered list items
        lines = text.strip().split("\n")
        return all(re.match(r"^[\s]*[-*•]|^\d+\.", line.strip()) for line in lines if line.strip())

    elif format_type == "code":
        # Check for code-like content (indentation, symbols)
        lines = text.strip().split("\n")
        return any(re.search(r"[{}\[\]()<>]|^\s{2,}|\t", line) for line in lines)

    return False


def detect_repetition(text: str, threshold: float = 0.3) -> bool:
    """Detect excessive repetition in text.

    Args:
        text: Text to analyze
        threshold: Maximum allowed repetition ratio

    Returns:
        True if excessive repetition detected, False otherwise
    """
    # Get word frequencies
    words = re.findall(r"\w+", text.lower())
    if not words:
        return False

    # Count unique vs total words
    unique_words = len(set(words))
    total_words = len(words)

    # Calculate repetition ratio
    repetition_ratio = 1 - (unique_words / total_words)

    return repetition_ratio > threshold


def check_balanced_delimiters(text: str) -> bool:
    """Check if delimiters (brackets, quotes) are balanced.

    Args:
        text: Text to check

    Returns:
        True if delimiters are balanced, False otherwise
    """
    stack = []
    pairs = {")": "(", "]": "[", "}": "{", '"': '"', "'": "'"}

    for char in text:
        if char in "([{\"'":
            stack.append(char)
        elif char in ")]}\"'":
            if not stack:
                return False
            if stack[-1] != pairs[char]:
                return False
            stack.pop()

    return len(stack) == 0
