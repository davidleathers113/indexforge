"""Text cleaning operations.

This module provides functions for cleaning and normalizing text content,
including whitespace handling and character normalization.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """Clean text by applying standard normalizations.

    Applies whitespace normalization and character normalization.

    Args:
        text: Text to clean

    Returns:
        Cleaned text

    Raises:
        ValueError: If text is None or empty
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    # Apply normalizations
    text = normalize_whitespace(text)
    text = normalize_characters(text)

    return text


def normalize_whitespace(text: str, preserve_paragraphs: bool = False) -> str:
    """Normalize whitespace in text.

    Args:
        text: Text to normalize
        preserve_paragraphs: Whether to preserve paragraph breaks

    Returns:
        Text with normalized whitespace

    Raises:
        ValueError: If text is None or empty
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    if preserve_paragraphs:
        # Replace multiple newlines with double newline
        text = re.sub(r"\n{2,}", "\n\n", text)
        # Replace single newlines with space
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    else:
        # Replace all whitespace with single space
        text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_characters(
    text: str, form: str = "NFKC", replace_quotes: bool = True, replace_dashes: bool = True
) -> str:
    """Normalize Unicode characters in text.

    Args:
        text: Text to normalize
        form: Unicode normalization form (NFC, NFKC, NFD, NFKD)
        replace_quotes: Whether to normalize quote characters
        replace_dashes: Whether to normalize dash characters

    Returns:
        Text with normalized characters

    Raises:
        ValueError: If text is None or empty or form is invalid
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    if form not in {"NFC", "NFKC", "NFD", "NFKD"}:
        raise ValueError(f"Invalid normalization form: {form}")

    # Apply Unicode normalization
    text = unicodedata.normalize(form, text)

    if replace_quotes:
        # Normalize quotes
        text = text.replace(""", '"').replace(""", '"')
        text = text.replace("'", "'").replace("'", "'")

    if replace_dashes:
        # Normalize dashes
        text = text.replace("–", "-").replace("—", "-")

    return text
