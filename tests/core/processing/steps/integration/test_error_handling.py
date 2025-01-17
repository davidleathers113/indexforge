"""Integration tests for error handling functionality."""

from datetime import UTC, datetime, timedelta

from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus


class TestErrorHandling:
    """Tests focused on error scenarios and logging."""

    def test_error_logging(self, step_manager: ProcessingStepManager) -> None:
        """Test error handling and logging integration."""
        error_msg = "Failed to process document"
        step_manager.add_step(
            doc_id="doc123",
            step_name="image_processing",
            status=ProcessingStatus.ERROR,
            details={"failed_pages": [1, 3]},
            error_message=error_msg,
        )

        steps = step_manager.get_steps("doc123")
        assert len(steps) == 1
        step = steps[0]
        assert step.status == ProcessingStatus.ERROR
        assert step.error_message == error_msg

    def test_recent_errors(self, step_manager: ProcessingStepManager) -> None:
        """Test recent errors aggregation across documents."""
        now = datetime.now(UTC)

        # Add errors for different documents
        for i, doc_id in enumerate(["doc1", "doc2", "doc3"]):
            step_manager.add_step(
                doc_id=doc_id,
                step_name=f"step_{i}",
                status=ProcessingStatus.ERROR,
                error_message=f"Error {i}",
                timestamp=now - timedelta(minutes=i * 30),
            )

        errors = step_manager.get_recent_errors(since=now - timedelta(hours=1))
        assert len(errors) == 3
        assert [e["doc_id"] for e in errors] == ["doc1", "doc2", "doc3"]
