"""Tests for version history models."""

from datetime import UTC, datetime

import pytest

from src.core.lineage.version.models import VersionTag
from src.core.lineage.version.types import VersionChangeType, VersionTagError


@pytest.fixture
def sample_tag_data():
    """Sample version tag data for testing."""
    return {
        "tag": "v1.0.0",
        "timestamp": "2024-01-17T12:00:00+00:00",
        "description": "Initial release",
        "author": "test.user",
        "change_type": "schema",
        "reliability_score": 0.95,
    }


def test_version_tag_creation():
    """Test basic version tag creation."""
    tag = VersionTag(
        tag="v1.0.0",
        description="Initial release",
        author="test.user",
        change_type=VersionChangeType.SCHEMA,
        reliability_score=0.95,
    )

    assert tag.tag == "v1.0.0"
    assert isinstance(tag.timestamp, datetime)
    assert tag.description == "Initial release"
    assert tag.author == "test.user"
    assert tag.change_type == VersionChangeType.SCHEMA
    assert tag.reliability_score == 0.95


def test_version_tag_defaults():
    """Test version tag default values."""
    tag = VersionTag(tag="v1.0.0")

    assert tag.tag == "v1.0.0"
    assert isinstance(tag.timestamp, datetime)
    assert tag.description == ""
    assert tag.author == ""
    assert tag.change_type == VersionChangeType.METADATA
    assert tag.reliability_score is None


def test_version_tag_to_dict(sample_tag_data):
    """Test converting version tag to dictionary."""
    tag = VersionTag.from_dict(sample_tag_data)
    data = tag.to_dict()

    assert data["tag"] == "v1.0.0"
    assert data["timestamp"] == "2024-01-17T12:00:00+00:00"
    assert data["description"] == "Initial release"
    assert data["author"] == "test.user"
    assert data["change_type"] == "schema"
    assert data["reliability_score"] == 0.95


def test_version_tag_from_dict(sample_tag_data):
    """Test creating version tag from dictionary."""
    tag = VersionTag.from_dict(sample_tag_data)

    assert tag.tag == "v1.0.0"
    assert tag.timestamp == datetime(2024, 1, 17, 12, 0, tzinfo=UTC)
    assert tag.description == "Initial release"
    assert tag.author == "test.user"
    assert tag.change_type == VersionChangeType.SCHEMA
    assert tag.reliability_score == 0.95


def test_version_tag_from_dict_invalid():
    """Test error handling for invalid dictionary data."""
    with pytest.raises(VersionTagError) as exc:
        VersionTag.from_dict({"tag": "v1.0.0", "timestamp": "invalid"})
    assert "Invalid version tag data" in str(exc.value)
