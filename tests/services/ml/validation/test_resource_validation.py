"""Tests for resource-aware validation.

This module contains tests for resource validation strategies.
"""

import pytest

from src.core.models.chunks import Chunk
from src.services.ml.monitoring.metrics import MetricsCollector, OperationMetrics
from src.services.ml.optimization.resources import ResourceManager
from src.services.ml.validation.resource_validation import (
    ResourceAwareValidator,
    ResourceValidationParameters,
)


@pytest.fixture
def metrics_collector(mocker):
    """Mock metrics collector."""
    collector = mocker.Mock(spec=MetricsCollector)
    collector.get_metrics.return_value = [
        OperationMetrics(
            name="operation_execution",
            duration_ms=1000.0,
            memory_mb=500.0,
            success=True,
        )
    ]
    return collector


@pytest.fixture
def resource_manager(mocker):
    """Mock resource manager."""
    manager = mocker.Mock(spec=ResourceManager)
    manager._get_memory_usage.return_value = 500.0
    return manager


@pytest.fixture
def validation_params():
    """Create validation parameters."""
    return ResourceValidationParameters(
        max_memory_mb=1000.0,
        max_batch_duration_ms=5000.0,
        min_success_rate=0.8,
        max_consecutive_failures=3,
    )


@pytest.fixture
def validator(metrics_collector, resource_manager, validation_params):
    """Create resource-aware validator."""
    return ResourceAwareValidator(metrics_collector, resource_manager, validation_params)


class TestResourceAwareValidator:
    """Tests for ResourceAwareValidator."""

    def test_validate_single_chunk_success(self, validator):
        """Test validating single chunk within limits."""
        chunk = Chunk(id="test", text="short text", metadata={})

        errors = validator.validate(chunk, validator._params)

        assert not errors

    def test_validate_single_chunk_memory_exceeded(self, validator, resource_manager):
        """Test validating single chunk exceeding memory."""
        resource_manager._get_memory_usage.return_value = 1500.0
        chunk = Chunk(id="test", text="short text", metadata={})

        errors = validator.validate(chunk, validator._params)

        assert len(errors) == 1
        assert "memory usage" in errors[0].lower()

    def test_validate_batch_success(self, validator):
        """Test validating batch within limits."""
        chunks = [
            Chunk(id="1", text="text 1", metadata={}),
            Chunk(id="2", text="text 2", metadata={}),
        ]

        errors = validator.validate(chunks, validator._params)

        assert not errors

    def test_validate_batch_memory_exceeded(self, validator):
        """Test validating batch exceeding memory."""
        # Create large chunks that will exceed memory limits
        large_text = "x" * 1000000  # 1MB of text
        chunks = [
            Chunk(id="1", text=large_text, metadata={}),
            Chunk(id="2", text=large_text, metadata={}),
        ]

        errors = validator.validate(chunks, validator._params)

        assert len(errors) == 1
        assert "memory requirement" in errors[0].lower()

    def test_validate_performance_degradation(self, validator, metrics_collector):
        """Test validation with poor performance metrics."""
        # Simulate slow operations
        metrics_collector.get_metrics.return_value = [
            OperationMetrics(
                name="operation_execution",
                duration_ms=6000.0,  # Exceeds max_batch_duration_ms
                memory_mb=500.0,
                success=True,
            )
        ]
        chunk = Chunk(id="test", text="test text", metadata={})

        errors = validator.validate(chunk, validator._params)

        assert len(errors) == 1
        assert "duration" in errors[0].lower()

    def test_validate_consecutive_failures(self, validator):
        """Test validation with consecutive failures."""
        chunk = Chunk(id="test", text="test text", metadata={})

        # Simulate multiple failures
        for _ in range(validator._params.max_consecutive_failures):
            validator._consecutive_failures += 1

        errors = validator.validate(chunk, validator._params)

        assert len(errors) == 1
        assert "consecutive" in errors[0].lower()

    def test_validate_success_rate(self, validator, metrics_collector):
        """Test validation with low success rate."""
        # Simulate operations with low success rate
        metrics_collector.get_metrics.return_value = [
            OperationMetrics(
                name="operation_execution",
                duration_ms=1000.0,
                memory_mb=500.0,
                success=False,
            ),
            OperationMetrics(
                name="operation_execution",
                duration_ms=1000.0,
                memory_mb=500.0,
                success=False,
            ),
        ]
        chunk = Chunk(id="test", text="test text", metadata={})

        errors = validator.validate(chunk, validator._params)

        assert len(errors) == 1
        assert "success rate" in errors[0].lower()
