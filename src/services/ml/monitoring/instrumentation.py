"""Performance instrumentation for ML services.

This module provides performance instrumentation capabilities, integrating
profiling and metrics collection for comprehensive performance monitoring.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.services.ml.errors import InstrumentationError
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.monitoring.profiler import OperationProfiler, ProfileMetrics
from src.services.ml.optimization.resources import ResourceManager

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Return type for instrumented operations


@dataclass
class InstrumentationConfig:
    """Configuration for performance instrumentation."""

    collect_profiles: bool = True
    track_resources: bool = True
    log_level: int = logging.INFO
    alert_thresholds: Dict[str, float] = None


class PerformanceInstrumentor:
    """Manages performance instrumentation for ML services."""

    def __init__(
        self,
        metrics: MetricsCollector,
        resources: ResourceManager,
        config: Optional[InstrumentationConfig] = None,
    ) -> None:
        """Initialize instrumentor.

        Args:
            metrics: Metrics collector for tracking
            resources: Resource manager for monitoring
            config: Optional instrumentation configuration
        """
        self._metrics = metrics
        self._resources = resources
        self._profiler = OperationProfiler(metrics)
        self._config = config or InstrumentationConfig()
        self._operation_history: List[ProfileMetrics] = []

    async def instrument(
        self, operation_name: str, operation: Callable[..., T], **kwargs: Any
    ) -> T:
        """Instrument an operation.

        Args:
            operation_name: Name of the operation
            operation: Operation to instrument
            **kwargs: Operation arguments

        Returns:
            Operation result

        Raises:
            InstrumentationError: If instrumentation fails
        """
        try:
            # Set up instrumentation
            logger.setLevel(self._config.log_level)
            logger.info(f"Starting instrumentation for {operation_name}")

            # Profile and monitor operation
            with self._profiler.profile(operation_name):
                if self._config.track_resources:
                    result = await self._resources.execute_with_resources(
                        lambda: operation(**kwargs),
                        required_mb=self._estimate_memory_requirement(kwargs),
                    )
                else:
                    result = await operation(**kwargs)

            # Check thresholds
            self._check_thresholds(operation_name)

            return result

        except Exception as e:
            logger.exception(f"Instrumentation failed for {operation_name}")
            raise InstrumentationError(
                f"Failed to instrument {operation_name}",
                details={"operation": operation_name, "error": str(e)},
            ) from e

    def get_operation_history(self) -> List[ProfileMetrics]:
        """Get operation execution history.

        Returns:
            List of profile metrics
        """
        return self._profiler.get_active_profiles()

    def clear_history(self) -> None:
        """Clear operation history."""
        self._profiler.clear_profiles()

    def _estimate_memory_requirement(self, operation_args: Dict[str, Any]) -> float:
        """Estimate memory requirement for operation.

        Args:
            operation_args: Operation arguments

        Returns:
            Estimated memory requirement in MB
        """
        # Base memory requirement
        base_memory = 100.0  # MB

        # Add estimates based on argument types and sizes
        for arg in operation_args.values():
            if isinstance(arg, (list, tuple)):
                base_memory += len(arg) * 0.1  # 100KB per item
            elif isinstance(arg, dict):
                base_memory += len(arg) * 0.05  # 50KB per entry
            elif isinstance(arg, str):
                base_memory += len(arg) * 2 / 1024 / 1024  # 2 bytes per char

        return base_memory

    def _check_thresholds(self, operation_name: str) -> None:
        """Check performance thresholds.

        Args:
            operation_name: Operation to check
        """
        if not self._config.alert_thresholds:
            return

        profiles = self._profiler.get_active_profiles()
        if not profiles:
            return

        latest = profiles[-1]
        thresholds = self._config.alert_thresholds

        # Check duration threshold
        if "duration_ms" in thresholds and latest.duration_ms > thresholds["duration_ms"]:
            logger.warning(
                f"Operation {operation_name} exceeded duration threshold: "
                f"{latest.duration_ms:.1f}ms > {thresholds['duration_ms']}ms"
            )

        # Check memory threshold
        if "memory_mb" in thresholds and latest.memory_mb > thresholds["memory_mb"]:
            logger.warning(
                f"Operation {operation_name} exceeded memory threshold: "
                f"{latest.memory_mb:.1f}MB > {thresholds['memory_mb']}MB"
            )

        # Check CPU threshold
        if "cpu_percent" in thresholds and latest.cpu_percent > thresholds["cpu_percent"]:
            logger.warning(
                f"Operation {operation_name} exceeded CPU threshold: "
                f"{latest.cpu_percent:.1f}% > {thresholds['cpu_percent']}%"
            )
