"""Tests for version history type definitions."""

import pytest

from src.core.lineage.version.types import VersionChangeType, VersionError, VersionTagError


def test_version_error_inheritance():
    """Verify error class inheritance hierarchy."""
    assert issubclass(VersionTagError, VersionError)
    assert issubclass(VersionError, Exception)


@pytest.mark.parametrize(
    "change_type,expected_value",
    [
        (VersionChangeType.SCHEMA, "schema"),
        (VersionChangeType.CONFIG, "config"),
        (VersionChangeType.CONTENT, "content"),
        (VersionChangeType.METADATA, "metadata"),
        (VersionChangeType.PROPERTY, "property"),
        (VersionChangeType.VECTORIZER, "vectorizer"),
    ],
)
def test_version_change_type_values(change_type: VersionChangeType, expected_value: str):
    """Verify version change type enum values."""
    assert change_type.value == expected_value


def test_version_change_type_uniqueness():
    """Verify version change type values are unique."""
    values = [t.value for t in VersionChangeType]
    assert len(values) == len(set(values)), "Duplicate values found in VersionChangeType"
