import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, TypeVar

import numpy as np
import psutil

T = TypeVar("T")


class PerformanceMetrics:
    def __init__(self, operation_name: str, metrics_path: Path):
        self.operation_name = operation_name
        self.metrics_path = metrics_path
        self.durations_ms: List[float] = []
        self.memory_samples_mb: List[float] = []
        self.cpu_samples: List[float] = []
        self.network_io_samples: List[Dict[str, int]] = []
        self.disk_io_samples: List[Dict[str, int]] = []
        self._start_time: float = 0
        self._start_memory: float = 0
        self._start_network_io: Dict[str, int] = {}
        self._start_disk_io: Dict[str, int] = {}
        self._process = psutil.Process()

    def start_operation(self) -> None:
        """Start timing an operation and record initial system metrics."""
        self._start_time = time.perf_counter()
        self._start_memory = self._process.memory_info().rss / (1024 * 1024)

        # Capture initial I/O counters
        net_io = psutil.net_io_counters()
        self._start_network_io = {"bytes_sent": net_io.bytes_sent, "bytes_recv": net_io.bytes_recv}

        disk_io = psutil.disk_io_counters()
        self._start_disk_io = {"read_bytes": disk_io.read_bytes, "write_bytes": disk_io.write_bytes}

    def end_operation(self) -> None:
        """End timing an operation and record final system metrics."""
        # Duration
        duration = (time.perf_counter() - self._start_time) * 1000
        self.durations_ms.append(duration)

        # Memory
        end_memory = self._process.memory_info().rss / (1024 * 1024)
        self.memory_samples_mb.append(end_memory - self._start_memory)

        # CPU
        self.cpu_samples.append(self._process.cpu_percent())

        # Network I/O
        net_io = psutil.net_io_counters()
        self.network_io_samples.append(
            {
                "bytes_sent": net_io.bytes_sent - self._start_network_io["bytes_sent"],
                "bytes_recv": net_io.bytes_recv - self._start_network_io["bytes_recv"],
            }
        )

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        self.disk_io_samples.append(
            {
                "read_bytes": disk_io.read_bytes - self._start_disk_io["read_bytes"],
                "write_bytes": disk_io.write_bytes - self._start_disk_io["write_bytes"],
            }
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics."""
        if not self.durations_ms:
            return {}

        duration_percentiles = np.percentile(self.durations_ms, [50, 95, 99])
        memory_percentiles = np.percentile(self.memory_samples_mb, [50, 95, 99])
        cpu_percentiles = (
            np.percentile(self.cpu_samples, [50, 95, 99]) if self.cpu_samples else [0, 0, 0]
        )

        # Calculate I/O statistics
        network_sent = [sample["bytes_sent"] for sample in self.network_io_samples]
        network_recv = [sample["bytes_recv"] for sample in self.network_io_samples]
        disk_read = [sample["read_bytes"] for sample in self.disk_io_samples]
        disk_write = [sample["write_bytes"] for sample in self.disk_io_samples]

        return {
            "operation": self.operation_name,
            "samples": len(self.durations_ms),
            "duration_ms": {
                "min": min(self.durations_ms),
                "max": max(self.durations_ms),
                "mean": statistics.mean(self.durations_ms),
                "p50": duration_percentiles[0],
                "p95": duration_percentiles[1],
                "p99": duration_percentiles[2],
            },
            "memory_mb": {
                "min": min(self.memory_samples_mb),
                "max": max(self.memory_samples_mb),
                "mean": statistics.mean(self.memory_samples_mb),
                "p50": memory_percentiles[0],
                "p95": memory_percentiles[1],
                "p99": memory_percentiles[2],
            },
            "cpu_percent": {
                "min": min(self.cpu_samples) if self.cpu_samples else 0,
                "max": max(self.cpu_samples) if self.cpu_samples else 0,
                "mean": statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
                "p50": cpu_percentiles[0],
                "p95": cpu_percentiles[1],
                "p99": cpu_percentiles[2],
            },
            "network_io": {
                "bytes_sent": {
                    "total": sum(network_sent),
                    "mean": statistics.mean(network_sent),
                    "max": max(network_sent),
                },
                "bytes_recv": {
                    "total": sum(network_recv),
                    "mean": statistics.mean(network_recv),
                    "max": max(network_recv),
                },
            },
            "disk_io": {
                "read_bytes": {
                    "total": sum(disk_read),
                    "mean": statistics.mean(disk_read),
                    "max": max(disk_read),
                },
                "write_bytes": {
                    "total": sum(disk_write),
                    "mean": statistics.mean(disk_write),
                    "max": max(disk_write),
                },
            },
        }

    def save_metrics(self) -> None:
        """Save performance metrics to file."""
        stats = self.get_statistics()
        if not stats:
            return

        metrics_file = self.metrics_path / f"{self.operation_name}_metrics.json"
        metrics_file.write_text(json.dumps(stats, indent=2))


async def measure_async_operation(
    operation: Callable[..., Awaitable[T]], metrics: PerformanceMetrics, *args, **kwargs
) -> T:
    """Measure performance of an async operation."""
    metrics.start_operation()
    try:
        result = await operation(*args, **kwargs)
        return result
    finally:
        metrics.end_operation()


def measure_sync_operation(
    operation: Callable[..., T], metrics: PerformanceMetrics, *args, **kwargs
) -> T:
    """Measure performance of a sync operation."""
    metrics.start_operation()
    try:
        result = operation(*args, **kwargs)
        return result
    finally:
        metrics.end_operation()
