"""Tests for parameter normalizers."""

import pytest

from src.pipeline.parameters.normalizers.type_coercion import TypeCoercionNormalizer
from src.pipeline.parameters.normalizers.url import URLNormalizer

from .errors import ValidationError


class TestTypeCoercionNormalizer:
    """Tests for TypeCoercionNormalizer."""

    def test_none_allowed(self):
        """Test normalization when None is allowed."""
        normalizer = TypeCoercionNormalizer(allow_none=True)
        assert normalizer.normalize(None) is None

    def test_none_not_allowed(self):
        """Test normalization when None is not allowed."""
        normalizer = TypeCoercionNormalizer(allow_none=False)
        with pytest.raises(ValidationError):
            normalizer.normalize(None)

    def test_string_normalization(self):
        """Test string normalization."""
        normalizer = TypeCoercionNormalizer()
        assert normalizer.normalize("test") == "test"
        assert normalizer.normalize(" test ") == "test"

    def test_integer_normalization(self):
        """Test integer normalization."""
        normalizer = TypeCoercionNormalizer()
        assert normalizer.normalize("42") == "42"
        assert normalizer.normalize(42) == "42"

    def test_float_normalization(self):
        """Test float normalization."""
        normalizer = TypeCoercionNormalizer()
        assert normalizer.normalize("3.14") == "3.14"
        assert normalizer.normalize(3.14) == "3.14"


class TestURLNormalizer:
    """Tests for URLNormalizer."""

    def test_valid_url(self):
        """Test normalization of valid URLs."""
        normalizer = URLNormalizer()
        assert normalizer.normalize("https://example.com") == "https://example.com"

    def test_url_with_params(self):
        """Test normalization of URLs with query parameters."""
        normalizer = URLNormalizer()
        assert (
            normalizer.normalize("https://example.com?key=value") == "https://example.com?key=value"
        )

    def test_url_with_fragment(self):
        """Test normalization of URLs with fragments."""
        normalizer = URLNormalizer()
        assert normalizer.normalize("https://example.com#section") == "https://example.com#section"

    def test_invalid_url(self):
        """Test normalization of invalid URLs."""
        normalizer = URLNormalizer()
        with pytest.raises(ValidationError):
            normalizer.normalize("not a url")

    def test_url_with_spaces(self):
        """Test normalization of URLs with spaces."""
        normalizer = URLNormalizer()
        with pytest.raises(ValidationError):
            normalizer.normalize("https://example.com/path with spaces")
