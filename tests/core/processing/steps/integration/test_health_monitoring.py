"""Integration tests for health monitoring functionality."""

from datetime import UTC, datetime

from src.core.monitoring.health.models.status import HealthStatus
from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus


class TestHealthMonitoring:
    """Tests focused on health check integration."""

    def test_health_check(
        self,
        step_manager: ProcessingStepManager,
        mock_health_manager,
    ) -> None:
        """Test integration with health monitoring."""
        doc_id = "doc123"
        now = datetime.now(UTC)

        step_manager.add_step(
            doc_id=doc_id,
            step_name="error_step",
            status=ProcessingStatus.ERROR,
            error_message="Test error",
            timestamp=now,
        )

        mock_health_manager.perform_health_check.return_value.status = HealthStatus.WARNING
        result = mock_health_manager.perform_health_check()
        assert result.status == HealthStatus.WARNING
