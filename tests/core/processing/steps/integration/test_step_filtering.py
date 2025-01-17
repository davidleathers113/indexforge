"""Integration tests for step filtering functionality."""

from datetime import UTC, datetime, timedelta

from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus


class TestStepFiltering:
    """Tests focused on step filtering and querying."""

    def test_time_based_filtering(self, step_manager: ProcessingStepManager) -> None:
        """Test filtering steps by time range."""
        doc_id = "doc123"
        now = datetime.now(UTC)

        step_manager.add_step(
            doc_id=doc_id,
            step_name="old_step",
            status=ProcessingStatus.SUCCESS,
            timestamp=now - timedelta(hours=2),
        )
        step_manager.add_step(
            doc_id=doc_id,
            step_name="recent_step",
            status=ProcessingStatus.SUCCESS,
            timestamp=now,
        )

        recent_steps = step_manager.get_steps(
            doc_id=doc_id,
            start_time=now - timedelta(hours=1),
        )
        assert len(recent_steps) == 1
        assert recent_steps[0].step_name == "recent_step"

    def test_status_filtering(self, step_manager: ProcessingStepManager) -> None:
        """Test filtering steps by status."""
        doc_id = "doc123"
        now = datetime.now(UTC)

        step_manager.add_step(
            doc_id=doc_id,
            step_name="error_step",
            status=ProcessingStatus.ERROR,
            timestamp=now,
        )
        step_manager.add_step(
            doc_id=doc_id,
            step_name="success_step",
            status=ProcessingStatus.SUCCESS,
            timestamp=now,
        )

        error_steps = step_manager.get_steps(
            doc_id=doc_id,
            status=ProcessingStatus.ERROR,
        )
        assert len(error_steps) == 1
        assert error_steps[0].step_name == "error_step"
