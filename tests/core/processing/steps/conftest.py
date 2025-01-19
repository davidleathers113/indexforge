"""Shared fixtures for processing steps tests."""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest


class MockLineage:
    """Mock document lineage for testing."""

    def __init__(self) -> None:
        self.processing_steps = []
        self.error_logs = []
        self.last_modified = datetime.now(UTC)


class MockStorage:
    """Mock storage backend for testing."""

    def __init__(self) -> None:
        self.lineage_data: dict[str, MockLineage] = {}

    def get_lineage(self, doc_id: str) -> MockLineage:
        if doc_id not in self.lineage_data:
            self.lineage_data[doc_id] = MockLineage()
        return self.lineage_data[doc_id]

    def save_lineage(self, lineage: MockLineage) -> None:
        pass

    def get_all_lineage(self) -> dict[str, MockLineage]:
        return self.lineage_data


@pytest.fixture
def storage() -> MockStorage:
    """Create a mock storage instance."""
    return MockStorage()


@pytest.fixture
def step_manager(storage: MockStorage) -> Generator:
    """Create a processing step manager instance."""
    from src.core.processing.steps.lifecycle.manager import ProcessingStepManager

    manager = ProcessingStepManager(storage)
    yield manager
    # Cleanup after each test
    storage.lineage_data.clear()


@pytest.fixture
def mock_health_manager() -> Generator:
    """Create a mock health check manager."""
    from unittest.mock import patch

    with patch("src.core.monitoring.health.lifecycle.manager.HealthCheckManager") as mock:
        yield mock.return_value
