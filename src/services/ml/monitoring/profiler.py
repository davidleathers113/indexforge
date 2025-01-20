"""Performance profiling for ML services.

This module provides detailed performance profiling capabilities for ML operations,
tracking execution time, memory usage, and resource utilization.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional

import psutil

from src.services.ml.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class ProfileMetrics:
    """Detailed performance metrics for an operation."""

    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    cpu_percent: float
    memory_mb: float
    thread_count: int
    context_switches: int
    io_counters: Dict[str, int]
    gpu_memory_mb: Optional[float] = None


class OperationProfiler:
    """Profiles ML operations for performance monitoring."""

    def __init__(self, metrics: MetricsCollector):
        """Initialize profiler.

        Args:
            metrics: Metrics collector for tracking
        """
        self._metrics = metrics
        self._process = psutil.Process()
        self._active_profiles: List[ProfileMetrics] = []

    @contextmanager
    def profile(self, operation_name: str):
        """Profile an operation.

        Args:
            operation_name: Name of the operation to profile

        Yields:
            None
        """
        try:
            # Start profiling
            start_time = time.time()
            start_cpu = self._process.cpu_percent()
            start_io = self._process.io_counters()
            initial_ctx = self._process.num_ctx_switches()

            yield

        except Exception as e:
            logger.exception(f"Error during profiling of {operation_name}")
            raise e

        finally:
            # Collect end metrics
            end_time = time.time()
            end_cpu = self._process.cpu_percent()
            end_io = self._process.io_counters()
            final_ctx = self._process.num_ctx_switches()

            # Calculate metrics
            duration_ms = (end_time - start_time) * 1000
            cpu_percent = (end_cpu + start_cpu) / 2
            memory_mb = self._process.memory_info().rss / 1024 / 1024
            thread_count = self._process.num_threads()
            context_switches = (
                final_ctx.voluntary
                + final_ctx.involuntary
                - initial_ctx.voluntary
                - initial_ctx.involuntary
            )
            io_counters = {
                "read_bytes": end_io.read_bytes - start_io.read_bytes,
                "write_bytes": end_io.write_bytes - start_io.write_bytes,
            }

            # Create profile
            profile = ProfileMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                thread_count=thread_count,
                context_switches=context_switches,
                io_counters=io_counters,
            )

            # Try to collect GPU metrics if available
            try:
                import torch

                if torch.cuda.is_available():
                    profile.gpu_memory_mb = torch.cuda.memory_allocated() / 1024 / 1024
            except ImportError:
                pass

            # Store and report metrics
            self._active_profiles.append(profile)
            self._report_metrics(profile)

    def _report_metrics(self, profile: ProfileMetrics) -> None:
        """Report profile metrics.

        Args:
            profile: Profile metrics to report
        """
        # Log detailed metrics
        logger.info(
            f"Operation {profile.operation_name} completed:\n"
            f"  Duration: {profile.duration_ms:.2f}ms\n"
            f"  CPU: {profile.cpu_percent:.1f}%\n"
            f"  Memory: {profile.memory_mb:.1f}MB\n"
            f"  Threads: {profile.thread_count}\n"
            f"  Context Switches: {profile.context_switches}"
        )

        # Track in metrics collector
        metadata = {
            "cpu_percent": profile.cpu_percent,
            "thread_count": profile.thread_count,
            "context_switches": profile.context_switches,
            "gpu_memory_mb": profile.gpu_memory_mb,
        }
        if profile.io_counters:
            metadata.update(profile.io_counters)

        self._metrics.record_metric(
            name=profile.operation_name,
            duration_ms=profile.duration_ms,
            memory_mb=profile.memory_mb,
            metadata=metadata,
        )

    def get_active_profiles(self) -> List[ProfileMetrics]:
        """Get currently active profiles.

        Returns:
            List of active profile metrics
        """
        return self._active_profiles.copy()

    def clear_profiles(self) -> None:
        """Clear stored profiles."""
        self._active_profiles.clear()
