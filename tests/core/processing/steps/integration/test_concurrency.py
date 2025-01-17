"""Integration tests for concurrent processing functionality."""

from datetime import UTC, datetime, timedelta

from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus


class TestConcurrency:
    """Tests focused on concurrent operations."""

    def test_concurrent_steps(self, step_manager: ProcessingStepManager) -> None:
        """Test handling of concurrent processing steps."""
        doc_id = "doc123"
        now = datetime.now(UTC)

        # Add parallel steps
        for i in range(2):
            step_manager.add_step(
                doc_id=doc_id,
                step_name=f"parallel_step{i}",
                status=ProcessingStatus.RUNNING,
                timestamp=now,
            )

        running_steps = step_manager.get_steps(
            doc_id=doc_id,
            status=ProcessingStatus.RUNNING,
        )
        assert len(running_steps) == 2

        # Complete one step
        step_manager.add_step(
            doc_id=doc_id,
            step_name="parallel_step0",
            status=ProcessingStatus.SUCCESS,
            timestamp=now + timedelta(seconds=1),
        )

        success_steps = step_manager.get_steps(
            doc_id=doc_id,
            status=ProcessingStatus.SUCCESS,
        )
        assert len(success_steps) == 1
