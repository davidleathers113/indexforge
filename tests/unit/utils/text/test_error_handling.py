"""Tests for text processing error handling."""
from unittest.mock import Mock, patch
import pytest
from src.utils.text_processing import clean_text

def test_clean_text():
    """Test text cleaning functionality."""
    text = '\n    This is a\n    multiline text   with\n    extra   spaces\n    '
    cleaned = clean_text(text)
    assert cleaned == 'This is a multiline text with extra spaces'
    assert '  ' not in cleaned
    assert '\n' not in cleaned

def test_clean_text_empty():
    """Test cleaning empty text."""
    assert clean_text('') == ''
    assert clean_text(None) == ''

def test_clean_text_whitespace_only():
    """Test cleaning whitespace-only text."""
    assert clean_text('   \n  \t  ') == ''