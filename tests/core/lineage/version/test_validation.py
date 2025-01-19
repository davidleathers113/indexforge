"""Tests for version validation functionality."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.core.lineage.version.models import Change, VersionTag
from src.core.lineage.version.types import VersionChangeType
from src.core.lineage.version.validation import VersionValidationError, VersionValidator


@pytest.fixture
def sample_change():
    """Create a sample change for testing."""
    return Change(
        id=uuid4(),
        timestamp=datetime.now(),
        change_type=VersionChangeType.CONTENT,
        description="Test change",
        author="test_user",
        diff="test diff",
        metadata={},
        parent_id=None,
        reliability_score=0.95,
    )


@pytest.fixture
def sample_version_tag(sample_change):
    """Create a sample version tag for testing."""
    return VersionTag(
        tag="v1.0.0",
        description="Initial version",
        author="test_user",
        change_type=VersionChangeType.CONTENT,
        reliability_score=0.95,
        changes=[sample_change],
    )


def test_validate_version_tag_valid(sample_version_tag):
    """Test validation of a valid version tag."""
    # Should not raise any exceptions
    VersionValidator.validate_version_tag(sample_version_tag)


def test_validate_version_tag_invalid_tag():
    """Test validation fails with invalid tag format."""
    tag = sample_version_tag()
    tag.tag = "invalid tag"
    with pytest.raises(VersionValidationError, match="Invalid version tag format"):
        VersionValidator.validate_version_tag(tag)


def test_validate_version_tag_invalid_description():
    """Test validation fails with empty description."""
    tag = sample_version_tag()
    tag.description = ""
    with pytest.raises(VersionValidationError, match="Description cannot be empty"):
        VersionValidator.validate_version_tag(tag)


def test_validate_version_tag_invalid_reliability():
    """Test validation fails with invalid reliability score."""
    tag = sample_version_tag()
    tag.reliability_score = 1.5
    with pytest.raises(VersionValidationError, match="Reliability score must be between 0 and 1"):
        VersionValidator.validate_version_tag(tag)


def test_validate_change_valid(sample_change):
    """Test validation of a valid change."""
    # Should not raise any exceptions
    VersionValidator.validate_change(sample_change)


def test_validate_change_invalid_description():
    """Test validation fails with empty description."""
    change = sample_change()
    change.description = ""
    with pytest.raises(VersionValidationError, match="Change description cannot be empty"):
        VersionValidator.validate_change(change)


def test_validate_change_invalid_reliability():
    """Test validation fails with invalid reliability score."""
    change = sample_change()
    change.reliability_score = -0.5
    with pytest.raises(VersionValidationError, match="Reliability score must be between 0 and 1"):
        VersionValidator.validate_change(change)


def test_validate_change_invalid_metadata():
    """Test validation fails with invalid metadata."""
    change = sample_change()
    change.metadata = {"invalid": lambda x: x}  # Non-serializable metadata
    with pytest.raises(VersionValidationError, match="Metadata must be JSON serializable"):
        VersionValidator.validate_change(change)


def test_validate_change_sequence_valid():
    """Test validation of a valid change sequence."""
    base_time = datetime.now()
    changes = [
        Change(
            id=uuid4(),
            timestamp=base_time + timedelta(hours=i),
            change_type=VersionChangeType.CONTENT,
            description=f"Change {i}",
            author="test_user",
            diff=f"diff {i}",
            metadata={},
            parent_id=None,
            reliability_score=0.95,
        )
        for i in range(3)
    ]
    # Should not raise any exceptions
    VersionValidator.validate_change_sequence(changes)


def test_validate_change_sequence_invalid_order():
    """Test validation fails with out of order timestamps."""
    base_time = datetime.now()
    changes = [
        Change(
            id=uuid4(),
            timestamp=base_time - timedelta(hours=i),  # Decreasing timestamps
            change_type=VersionChangeType.CONTENT,
            description=f"Change {i}",
            author="test_user",
            diff=f"diff {i}",
            metadata={},
            parent_id=None,
            reliability_score=0.95,
        )
        for i in range(3)
    ]
    with pytest.raises(VersionValidationError, match="Changes must be in chronological order"):
        VersionValidator.validate_change_sequence(changes)


def test_validate_version_sequence_valid():
    """Test validation of a valid version sequence."""
    base_time = datetime.now()
    tags = [
        VersionTag(
            tag=f"v1.0.{i}",
            description=f"Version {i}",
            author="test_user",
            change_type=VersionChangeType.CONTENT,
            timestamp=base_time + timedelta(hours=i),
            reliability_score=0.95,
            changes=[],
        )
        for i in range(3)
    ]
    # Should not raise any exceptions
    VersionValidator.validate_version_sequence(tags)


def test_validate_version_sequence_invalid_order():
    """Test validation fails with out of order timestamps."""
    base_time = datetime.now()
    tags = [
        VersionTag(
            tag=f"v1.0.{i}",
            description=f"Version {i}",
            author="test_user",
            change_type=VersionChangeType.CONTENT,
            timestamp=base_time - timedelta(hours=i),  # Decreasing timestamps
            reliability_score=0.95,
            changes=[],
        )
        for i in range(3)
    ]
    with pytest.raises(VersionValidationError, match="Version tags must be in chronological order"):
        VersionValidator.validate_version_sequence(tags)


def test_validate_version_sequence_duplicate_tags():
    """Test validation fails with duplicate tags."""
    base_time = datetime.now()
    tags = [
        VersionTag(
            tag="v1.0.0",  # Same tag
            description=f"Version {i}",
            author="test_user",
            change_type=VersionChangeType.CONTENT,
            timestamp=base_time + timedelta(hours=i),
            reliability_score=0.95,
            changes=[],
        )
        for i in range(2)
    ]
    with pytest.raises(VersionValidationError, match="Duplicate version tags found"):
        VersionValidator.validate_version_sequence(tags)
