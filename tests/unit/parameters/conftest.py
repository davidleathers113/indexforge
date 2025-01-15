"""Test configuration for parameter unit tests."""

import pytest

from .errors import ValidationError


@pytest.fixture
def validation_error():
    """Fixture providing the ValidationError class."""
    return ValidationError


@pytest.fixture
def sample_parameter_values():
    """Fixture providing common parameter test values."""
    return {
        "string": "test_value",
        "integer": 42,
        "float": 3.14,
        "url": "https://example.com",
        "none": None,
    }
