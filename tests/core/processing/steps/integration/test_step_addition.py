"""Integration tests for step addition functionality."""

from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus


class TestStepAddition:
    """Tests focused on adding and retrieving steps."""

    def test_add_step(self, step_manager: ProcessingStepManager) -> None:
        """Test adding a processing step with storage integration."""
        step_manager.add_step(
            doc_id="doc123",
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"chars": 5000},
            metrics={"duration_ms": 1500},
        )

        steps = step_manager.get_steps("doc123")
        assert len(steps) == 1
        step = steps[0]
        assert step.step_name == "text_extraction"
        assert step.status == ProcessingStatus.SUCCESS
        assert step.details == {"chars": 5000}
        assert step.duration_ms == 1500
