"""Tests for log filtering functionality."""

from datetime import datetime, timedelta, timezone

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel
from src.connectors.direct_documentation_indexing.source_tracking.error_logging import (
    DocumentErrorLogger,
    LogEntry,
)


@pytest.fixture
def populated_logger(error_logger, sample_document):
    """Create a logger with sample log entries."""
    now = datetime.now(timezone.utc)

    # Add logs at different times with different levels
    error_logger.log_error(
        sample_document.id,
        "Old error",
        metadata={"source": "test1"},
        timestamp=now - timedelta(hours=2),
    )
    error_logger.log_warning(
        sample_document.id,
        "Old warning",
        metadata={"source": "test2"},
        timestamp=now - timedelta(hours=1),
    )
    error_logger.log_error(
        sample_document.id, "Recent error", metadata={"source": "test3"}, timestamp=now
    )

    return error_logger


def test_filter_by_time_range(populated_logger, sample_document):
    """Test filtering logs by time range."""
    now = datetime.now(timezone.utc)

    # Get logs from last hour
    recent_logs = populated_logger.get_logs(
        sample_document.id, start_time=now - timedelta(minutes=30)
    )
    assert len(recent_logs) == 1, "Should only get most recent log"
    assert recent_logs[0].message == "Recent error", "Should get correct log"

    # Get logs from last 2 hours
    mid_logs = populated_logger.get_logs(
        sample_document.id, start_time=now - timedelta(hours=1, minutes=30)
    )
    assert len(mid_logs) == 2, "Should get two most recent logs"

    # Get logs with end time
    old_logs = populated_logger.get_logs(sample_document.id, end_time=now - timedelta(minutes=30))
    assert len(old_logs) == 2, "Should get two oldest logs"


def test_filter_by_level(populated_logger, sample_document):
    """Test filtering logs by log level."""
    error_logs = populated_logger.get_logs(sample_document.id, log_level=LogLevel.ERROR)
    assert len(error_logs) == 2, "Should get all ERROR logs"
    assert all(log.log_level == LogLevel.ERROR for log in error_logs), "Should only get ERROR logs"

    warning_logs = populated_logger.get_logs(sample_document.id, log_level=LogLevel.WARNING)
    assert len(warning_logs) == 1, "Should get all WARNING logs"
    assert all(
        log.log_level == LogLevel.WARNING for log in warning_logs
    ), "Should only get WARNING logs"


def test_filter_by_metadata(populated_logger, sample_document):
    """Test filtering logs by metadata values."""
    test1_logs = populated_logger.get_logs(sample_document.id, metadata_filter={"source": "test1"})
    assert len(test1_logs) == 1, "Should get logs matching metadata"
    assert test1_logs[0].metadata["source"] == "test1", "Should get correct log"


def test_combined_filters(populated_logger, sample_document):
    """Test combining multiple filter criteria."""
    now = datetime.now(timezone.utc)

    filtered_logs = populated_logger.get_logs(
        sample_document.id,
        start_time=now - timedelta(hours=1, minutes=30),
        log_level=LogLevel.ERROR,
        metadata_filter={"source": "test3"},
    )

    assert len(filtered_logs) == 1, "Should get logs matching all criteria"
    assert filtered_logs[0].message == "Recent error", "Should get correct log"
    assert filtered_logs[0].metadata["source"] == "test3", "Should get correct log"


def test_filter_empty_results(populated_logger, sample_document):
    """Test filtering with criteria that match no logs."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)

    # Filter for future logs
    future_logs = populated_logger.get_logs(sample_document.id, start_time=future_time)
    assert len(future_logs) == 0, "Should get no logs from the future"

    # Filter with non-existent metadata
    no_match_logs = populated_logger.get_logs(
        sample_document.id, metadata_filter={"source": "non_existent"}
    )
    assert len(no_match_logs) == 0, "Should get no logs with non-existent metadata"
