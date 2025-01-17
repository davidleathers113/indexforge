"""Tests for LogEntry class functionality."""

from datetime import UTC, datetime

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.error_logging import LogEntry
from src.core.monitoring.errors.models.log_entry import LogLevel


@pytest.fixture
def sample_log_entry():
    """Create a sample log entry for testing."""
    return LogEntry(
        message="Test message",
        log_level=LogLevel.ERROR,
        timestamp=datetime.now(UTC),
        metadata={"key": "value"},
    )


def test_log_entry_creation():
    """Test creating a log entry with all fields."""
    timestamp = datetime.now(UTC)
    metadata = {"source": "test", "code": 123}

    entry = LogEntry(
        message="Test error", log_level=LogLevel.ERROR, timestamp=timestamp, metadata=metadata
    )

    assert entry.message == "Test error", "Message should be preserved"
    assert entry.log_level == LogLevel.ERROR, "Log level should be preserved"
    assert entry.timestamp == timestamp, "Timestamp should be preserved"
    assert entry.metadata == metadata, "Metadata should be preserved"


def test_log_entry_default_metadata():
    """Test log entry creation with default metadata."""
    entry = LogEntry(message="Test", log_level=LogLevel.WARNING, timestamp=datetime.now(UTC))

    assert entry.metadata == {}, "Default metadata should be empty dict"


def test_log_entry_serialization(sample_log_entry):
    """Test converting log entry to and from dictionary."""
    # Convert to dict
    entry_dict = sample_log_entry.to_dict()

    assert isinstance(entry_dict, dict), "Should convert to dictionary"
    assert entry_dict["message"] == sample_log_entry.message, "Message should be preserved"
    assert entry_dict["level"] == sample_log_entry.log_level.value, "Level should be preserved"
    assert entry_dict["metadata"] == sample_log_entry.metadata, "Metadata should be preserved"

    # Convert back to LogEntry
    new_entry = LogEntry.from_dict(entry_dict)
    assert new_entry.message == sample_log_entry.message, "Message should survive roundtrip"
    assert new_entry.log_level == sample_log_entry.log_level, "Level should survive roundtrip"
    assert new_entry.metadata == sample_log_entry.metadata, "Metadata should survive roundtrip"


def test_log_entry_invalid_level():
    """Test handling of invalid log levels."""
    with pytest.raises(ValueError):
        LogEntry(message="Test", log_level="INVALID", timestamp=datetime.now(UTC))
