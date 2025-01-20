"""Resource-aware validation for ML services.

This module provides validation strategies that consider resource constraints
and performance metrics when validating operations.
"""

import logging
from dataclasses import dataclass
from typing import Any, List

from src.core.models.chunks import Chunk
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager
from src.services.ml.validation.parameters import ValidationParameters
from src.services.ml.validation.strategies import ValidationStrategy

logger = logging.getLogger(__name__)


@dataclass
class ResourceValidationParameters(ValidationParameters):
    """Parameters for resource-aware validation."""

    max_memory_mb: float = 1000.0
    max_batch_duration_ms: float = 5000.0
    min_success_rate: float = 0.8
    max_consecutive_failures: int = 3


class ResourceAwareValidator(ValidationStrategy):
    """Validates operations considering resource constraints."""

    def __init__(
        self,
        metrics: MetricsCollector,
        resources: ResourceManager,
        params: ResourceValidationParameters,
    ) -> None:
        """Initialize validator.

        Args:
            metrics: Metrics collector for tracking
            resources: Resource manager for constraints
            params: Resource validation parameters
        """
        self._metrics = metrics
        self._resources = resources
        self._params = params
        self._consecutive_failures = 0

    def validate(self, data: Any, params: ValidationParameters) -> List[str]:
        """Validate operation against resource constraints.

        Args:
            data: Data to validate
            params: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            # Check current resource state
            self._validate_resource_state(errors)

            # Check operation-specific constraints
            if isinstance(data, List):
                self._validate_batch_operation(data, errors)
            elif isinstance(data, Chunk):
                self._validate_single_operation(data, errors)

            # Reset failure counter on success
            if not errors:
                self._consecutive_failures = 0

        except Exception as e:
            logger.exception("Resource validation failed")
            errors.append(f"Resource validation error: {str(e)}")
            self._consecutive_failures += 1

        # Check failure threshold
        if self._consecutive_failures >= self._params.max_consecutive_failures:
            errors.append(f"Operation failed {self._consecutive_failures} times consecutively")

        return errors

    def _validate_resource_state(self, errors: List[str]) -> None:
        """Validate current resource state.

        Args:
            errors: List to append validation errors to
        """
        current_memory = self._resources._get_memory_usage()
        if current_memory > self._params.max_memory_mb:
            errors.append(
                f"Current memory usage ({current_memory:.1f}MB) exceeds limit "
                f"({self._params.max_memory_mb}MB)"
            )

        # Check recent performance metrics
        recent_metrics = self._metrics.get_metrics("operation_execution")
        if recent_metrics:
            # Check average duration
            avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
            if avg_duration > self._params.max_batch_duration_ms:
                errors.append(
                    f"Average operation duration ({avg_duration:.1f}ms) exceeds limit "
                    f"({self._params.max_batch_duration_ms}ms)"
                )

            # Check success rate
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            if success_rate < self._params.min_success_rate:
                errors.append(
                    f"Operation success rate ({success_rate:.2%}) below threshold "
                    f"({self._params.min_success_rate:.2%})"
                )

    def _validate_batch_operation(self, items: List[Any], errors: List[str]) -> None:
        """Validate batch operation constraints.

        Args:
            items: Batch items to validate
            errors: List to append validation errors to
        """
        if not items:
            return

        # Estimate memory requirements
        if isinstance(items[0], Chunk):
            total_text_length = sum(len(chunk.text) for chunk in items)
            estimated_memory = (total_text_length * 2) / 1024 / 1024  # MB
            if estimated_memory > self._params.max_memory_mb:
                errors.append(
                    f"Estimated memory requirement ({estimated_memory:.1f}MB) exceeds limit "
                    f"({self._params.max_memory_mb}MB)"
                )

    def _validate_single_operation(self, item: Any, errors: List[str]) -> None:
        """Validate single operation constraints.

        Args:
            item: Item to validate
            errors: List to append validation errors to
        """
        if isinstance(item, Chunk):
            estimated_memory = (len(item.text) * 2) / 1024 / 1024  # MB
            if estimated_memory > self._params.max_memory_mb:
                errors.append(
                    f"Estimated memory requirement ({estimated_memory:.1f}MB) exceeds limit "
                    f"({self._params.max_memory_mb}MB)"
                )
