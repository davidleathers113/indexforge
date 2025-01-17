"""Storage management and monitoring functionality.

This module provides functionality for monitoring and managing storage usage
for document lineage data. It includes utilities for tracking disk space
usage, calculating storage metrics, and monitoring storage capacity.

Key Features:
    - Storage usage monitoring
    - Disk space tracking
    - Usage metrics calculation
    - Capacity monitoring
    - Storage statistics
    - Thread-safe operations

Example:
    ```python
    from pathlib import Path
    from src.core.storage.manager import StorageManager

    # Initialize storage manager
    manager = StorageManager(storage_path="/path/to/lineage/data")

    # Get storage metrics
    metrics = manager.get_storage_metrics()
    if metrics.percent_used > 80:
        print(f"Storage warning: {metrics.percent_used}% used")
        print(f"Available: {metrics.free_mb:.1f} MB")
    ```
"""

import logging
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class StorageMetrics:
    """Storage usage metrics."""

    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    timestamp: datetime

    @property
    def total_mb(self) -> float:
        """Total storage in megabytes."""
        return self.total_bytes / (1024 * 1024)

    @property
    def used_mb(self) -> float:
        """Used storage in megabytes."""
        return self.used_bytes / (1024 * 1024)

    @property
    def free_mb(self) -> float:
        """Free storage in megabytes."""
        return self.free_bytes / (1024 * 1024)


class StorageManager:
    """Manager for storage monitoring and metrics."""

    def __init__(self, storage_path: str | Path):
        """Initialize the storage manager.

        Args:
            storage_path: Path to the storage directory.
        """
        self.storage_path = Path(storage_path)
        self._metrics_cache: Optional[StorageMetrics] = None
        self._cache_lock = threading.Lock()
        self._cache_duration = timedelta(seconds=5)
        self._last_check = datetime.min.replace(tzinfo=UTC)

    def get_storage_metrics(self, use_cache: bool = True) -> StorageMetrics:
        """Get storage usage metrics.

        Args:
            use_cache: Whether to use cached metrics if available.

        Returns:
            StorageMetrics object containing usage information.

        Raises:
            OSError: If unable to access storage path.
        """
        now = datetime.now(UTC)

        # Check cache first
        if use_cache:
            with self._cache_lock:
                if (
                    self._metrics_cache is not None
                    and now - self._last_check < self._cache_duration
                ):
                    return self._metrics_cache

        # Ensure storage path exists
        if not self.storage_path.exists():
            raise OSError(f"Storage path does not exist: {self.storage_path}")

        try:
            # Get disk usage
            usage = psutil.disk_usage(str(self.storage_path))

            metrics = StorageMetrics(
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
                percent_used=usage.percent,
                timestamp=now,
            )

            # Update cache
            with self._cache_lock:
                self._metrics_cache = metrics
                self._last_check = now

            return metrics

        except Exception as e:
            logger.error(f"Error getting storage metrics: {e}")
            raise OSError(f"Failed to get storage metrics: {e}") from e

    def check_storage_threshold(
        self, threshold_percent: float = 80.0, use_cache: bool = True
    ) -> bool:
        """Check if storage usage exceeds the specified threshold.

        Args:
            threshold_percent: Storage usage threshold percentage.
            use_cache: Whether to use cached metrics if available.

        Returns:
            True if storage usage exceeds threshold, False otherwise.
        """
        metrics = self.get_storage_metrics(use_cache=use_cache)
        return metrics.percent_used > threshold_percent

    def get_directory_size(self, path: Optional[Path] = None) -> int:
        """Calculate total size of a directory recursively.

        Args:
            path: Directory path to check. Defaults to storage_path.

        Returns:
            Total size in bytes.

        Raises:
            OSError: If unable to access directory.
        """
        target_path = path or self.storage_path

        if not target_path.exists():
            raise OSError(f"Path does not exist: {target_path}")

        try:
            total_size = 0
            for item in target_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size

        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
            raise OSError(f"Failed to calculate directory size: {e}") from e

    def cleanup_old_files(
        self, max_age: timedelta, pattern: str = "*.json", dry_run: bool = False
    ) -> Dict[str, int]:
        """Remove files older than specified age.

        Args:
            max_age: Maximum file age to keep.
            pattern: File pattern to match.
            dry_run: If True, only simulate deletion.

        Returns:
            Dict with counts of deleted and skipped files.

        Raises:
            OSError: If unable to access or delete files.
        """
        if not self.storage_path.exists():
            raise OSError(f"Storage path does not exist: {self.storage_path}")

        now = datetime.now(UTC)
        cutoff = now - max_age
        deleted = skipped = 0

        try:
            for item in self.storage_path.rglob(pattern):
                if not item.is_file():
                    continue

                mtime = datetime.fromtimestamp(item.stat().st_mtime, UTC)
                if mtime < cutoff:
                    if not dry_run:
                        item.unlink()
                    deleted += 1
                else:
                    skipped += 1

            return {"deleted": deleted, "skipped": skipped}

        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            raise OSError(f"Failed to cleanup old files: {e}") from e
