"""Tests for tracking model implementations.

This module verifies that tracking model implementations correctly satisfy
their protocols and handle data transformations properly.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.core.models.lineage import LogEntry as LogEntryProtocol
from src.core.models.lineage import ProcessingStep as ProcessingStepProtocol
from src.core.models.lineage import Transformation as TransformationProtocol
from src.core.tracking.models.tracking import (
    LogEntry,
    LogLevel,
    ProcessingStatus,
    ProcessingStep,
    Transformation,
    TransformationType,
)


class TestProtocolCompliance:
    """Verify that implementations satisfy their protocols."""

    def test_transformation_protocol(self):
        """Test that Transformation implements TransformationProtocol."""
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Test transform",
        )
        assert isinstance(transform, TransformationProtocol)
        assert hasattr(transform, "to_dict")
        assert hasattr(transform, "from_dict")

    def test_processing_step_protocol(self):
        """Test that ProcessingStep implements ProcessingStepProtocol."""
        step = ProcessingStep(
            step_name="test_step",
            status=ProcessingStatus.SUCCESS,
        )
        assert isinstance(step, ProcessingStepProtocol)
        assert hasattr(step, "to_dict")
        assert hasattr(step, "from_dict")

    def test_log_entry_protocol(self):
        """Test that LogEntry implements LogEntryProtocol."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
        )
        assert isinstance(entry, LogEntryProtocol)
        assert hasattr(entry, "to_dict")
        assert hasattr(entry, "from_dict")


class TestTransformation:
    """Test Transformation implementation."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now(UTC)
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Test transform",
            parameters={"key": "value"},
            timestamp=timestamp,
        )
        data = transform.to_dict()
        assert data["transform_type"] == "content"
        assert data["description"] == "Test transform"
        assert data["parameters"] == {"key": "value"}
        assert data["timestamp"] == timestamp.isoformat()

    def test_from_dict(self):
        """Test creation from dictionary."""
        timestamp = datetime.now(UTC)
        data = {
            "transform_type": "content",
            "description": "Test transform",
            "parameters": {"key": "value"},
            "timestamp": timestamp.isoformat(),
        }
        transform = Transformation.from_dict(data)
        assert transform.transform_type == TransformationType.CONTENT
        assert transform.description == "Test transform"
        assert transform.parameters == {"key": "value"}
        assert transform.timestamp == timestamp

    def test_invalid_transform_type(self):
        """Test handling of invalid transformation type."""
        with pytest.raises(ValueError):
            Transformation.from_dict(
                {
                    "transform_type": "invalid",
                    "description": "Test",
                }
            )


class TestProcessingStep:
    """Test ProcessingStep implementation."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        start_time = datetime.now(UTC)
        end_time = start_time + timedelta(seconds=10)
        step = ProcessingStep(
            step_name="test_step",
            status=ProcessingStatus.SUCCESS,
            details={"key": "value"},
            start_time=start_time,
            end_time=end_time,
            error=None,
        )
        data = step.to_dict()
        assert data["step_name"] == "test_step"
        assert data["status"] == "success"
        assert data["details"] == {"key": "value"}
        assert data["start_time"] == start_time.isoformat()
        assert data["end_time"] == end_time.isoformat()
        assert data["error"] is None

    def test_from_dict(self):
        """Test creation from dictionary."""
        start_time = datetime.now(UTC)
        end_time = start_time + timedelta(seconds=10)
        data = {
            "step_name": "test_step",
            "status": "success",
            "details": {"key": "value"},
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "error": None,
        }
        step = ProcessingStep.from_dict(data)
        assert step.step_name == "test_step"
        assert step.status == ProcessingStatus.SUCCESS
        assert step.details == {"key": "value"}
        assert step.start_time == start_time
        assert step.end_time == end_time
        assert step.error is None

    def test_invalid_status(self):
        """Test handling of invalid processing status."""
        with pytest.raises(ValueError):
            ProcessingStep.from_dict(
                {
                    "step_name": "test",
                    "status": "invalid",
                }
            )


class TestLogEntry:
    """Test LogEntry implementation."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now(UTC)
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            timestamp=timestamp,
            details={"key": "value"},
        )
        data = entry.to_dict()
        assert data["level"] == "info"
        assert data["message"] == "Test message"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["details"] == {"key": "value"}

    def test_from_dict(self):
        """Test creation from dictionary."""
        timestamp = datetime.now(UTC)
        data = {
            "level": "info",
            "message": "Test message",
            "timestamp": timestamp.isoformat(),
            "details": {"key": "value"},
        }
        entry = LogEntry.from_dict(data)
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.timestamp == timestamp
        assert entry.details == {"key": "value"}

    def test_invalid_level(self):
        """Test handling of invalid log level."""
        with pytest.raises(ValueError):
            LogEntry.from_dict(
                {
                    "level": "invalid",
                    "message": "Test",
                }
            )
