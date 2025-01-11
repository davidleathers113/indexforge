"""Tests for error logging operations."""

from datetime import datetime, timedelta, timezone

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel
from src.connectors.direct_documentation_indexing.source_tracking.error_logging import (
    DocumentErrorLogger,
)


@pytest.fixture
def error_logger(storage):
    """Create a document error logger instance."""
    return DocumentErrorLogger(storage)


def test_log_error(error_logger, sample_document):
    """Test logging an error for a document."""
    error_msg = "Test error message"
    metadata = {"source": "test_function"}

    error_logger.log_error(sample_document.id, error_msg, metadata)

    logs = error_logger.get_logs(sample_document.id)
    assert len(logs) == 1, "Should have one log entry"

    log = logs[0]
    assert log.message == error_msg, "Error message should be preserved"
    assert log.log_level == LogLevel.ERROR, "Log level should be ERROR"
    assert log.metadata == metadata, "Metadata should be preserved"


def test_log_warning(error_logger, sample_document):
    """Test logging a warning for a document."""
    warning_msg = "Test warning message"

    error_logger.log_warning(sample_document.id, warning_msg)

    logs = error_logger.get_logs(sample_document.id)
    assert len(logs) == 1, "Should have one log entry"
    assert logs[0].log_level == LogLevel.WARNING, "Log level should be WARNING"


def test_get_logs_time_filtered(error_logger, sample_document):
    """Test retrieving logs with time filtering."""
    # Log entries at different times
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)

    error_logger.log_error(sample_document.id, "Old error", timestamp=old_time)
    error_logger.log_error(sample_document.id, "New error", timestamp=now)

    # Get logs from last hour
    recent_logs = error_logger.get_logs(sample_document.id, start_time=now - timedelta(hours=1))

    assert len(recent_logs) == 1, "Should only get recent log"
    assert recent_logs[0].message == "New error", "Should get most recent error"


def test_get_logs_level_filtered(error_logger, sample_document):
    """Test retrieving logs filtered by log level."""
    error_logger.log_error(sample_document.id, "Test error")
    error_logger.log_warning(sample_document.id, "Test warning")

    error_logs = error_logger.get_logs(sample_document.id, log_level=LogLevel.ERROR)

    assert len(error_logs) == 1, "Should only get ERROR logs"
    assert error_logs[0].log_level == LogLevel.ERROR, "Should only get ERROR logs"


def test_clear_logs(error_logger, sample_document):
    """Test clearing logs for a document."""
    error_logger.log_error(sample_document.id, "Test error")
    error_logger.log_warning(sample_document.id, "Test warning")

    error_logger.clear_logs(sample_document.id)

    logs = error_logger.get_logs(sample_document.id)
    assert len(logs) == 0, "All logs should be cleared"
