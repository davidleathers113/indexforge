"""Tests for document lineage model.

This module verifies that DocumentLineage correctly integrates with
tracking model implementations and handles document history properly.
"""

from datetime import UTC, datetime

import pytest

from src.core.models.lineage import DocumentLineage
from src.core.tracking.models.tracking import (
    LogEntry,
    LogLevel,
    ProcessingStatus,
    ProcessingStep,
    Transformation,
    TransformationType,
)


@pytest.fixture
def sample_lineage():
    """Create a sample document lineage."""
    return DocumentLineage(
        doc_id="test-doc-123",
        origin_id="source-doc-456",
        origin_source="test-source",
        origin_type="pdf",
    )


class TestDocumentLineage:
    """Test DocumentLineage functionality."""

    def test_add_transformation(self, sample_lineage):
        """Test adding a transformation to document history."""
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Test transform",
            parameters={"key": "value"},
        )
        sample_lineage.transformations.append(transform)
        assert len(sample_lineage.transformations) == 1
        assert isinstance(sample_lineage.transformations[0], Transformation)
        assert sample_lineage.transformations[0].transform_type == TransformationType.CONTENT

    def test_add_processing_step(self, sample_lineage):
        """Test adding a processing step to document history."""
        step = ProcessingStep(
            step_name="test_step",
            status=ProcessingStatus.SUCCESS,
            details={"processed": True},
        )
        sample_lineage.processing_steps.append(step)
        assert len(sample_lineage.processing_steps) == 1
        assert isinstance(sample_lineage.processing_steps[0], ProcessingStep)
        assert sample_lineage.processing_steps[0].status == ProcessingStatus.SUCCESS

    def test_add_log_entry(self, sample_lineage):
        """Test adding a log entry to document history."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test log message",
            details={"context": "test"},
        )
        sample_lineage.error_logs.append(entry)
        assert len(sample_lineage.error_logs) == 1
        assert isinstance(sample_lineage.error_logs[0], LogEntry)
        assert sample_lineage.error_logs[0].level == LogLevel.INFO

    def test_document_relationships(self, sample_lineage):
        """Test managing document relationships."""
        child_id = "child-doc-789"
        sample_lineage.children.append(child_id)
        sample_lineage.derived_documents.append(child_id)

        assert child_id in sample_lineage.children
        assert child_id in sample_lineage.derived_documents
        assert len(sample_lineage.children) == 1
        assert len(sample_lineage.derived_documents) == 1

    def test_timestamps(self):
        """Test timestamp handling."""
        before = datetime.now(UTC)
        lineage = DocumentLineage(doc_id="test-doc")
        after = datetime.now(UTC)

        assert before <= lineage.created_at <= after
        assert before <= lineage.last_modified <= after
        assert lineage.created_at == lineage.last_modified

    def test_metadata_handling(self, sample_lineage):
        """Test metadata management."""
        sample_lineage.metadata["test_key"] = "test_value"
        sample_lineage.performance_metrics["processing_time"] = 1.23

        assert sample_lineage.metadata["test_key"] == "test_value"
        assert sample_lineage.performance_metrics["processing_time"] == 1.23

    def test_complete_document_history(self):
        """Test recording complete document processing history."""
        lineage = DocumentLineage(doc_id="test-doc")

        # Add transformation
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Content extraction",
            parameters={"format": "text"},
        )
        lineage.transformations.append(transform)

        # Add processing step
        step = ProcessingStep(
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"pages": 5},
        )
        lineage.processing_steps.append(step)

        # Add error log
        error = LogEntry(
            level=LogLevel.WARNING,
            message="Image skipped",
            details={"page": 3},
        )
        lineage.error_logs.append(error)

        # Verify complete history
        assert len(lineage.transformations) == 1
        assert len(lineage.processing_steps) == 1
        assert len(lineage.error_logs) == 1

        assert isinstance(lineage.transformations[0], Transformation)
        assert isinstance(lineage.processing_steps[0], ProcessingStep)
        assert isinstance(lineage.error_logs[0], LogEntry)
