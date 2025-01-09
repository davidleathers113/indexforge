"""
Document lineage storage management and monitoring.

This module provides functionality for monitoring and managing storage usage
for document lineage data. It includes utilities for tracking disk space
usage, calculating storage metrics, and monitoring storage capacity.

Key Features:
    - Storage usage monitoring
    - Disk space tracking
    - Usage metrics calculation
    - Capacity monitoring
    - Storage statistics

Example:
    ```python
    from pathlib import Path

    # Get storage metrics for lineage data
    storage_path = Path("/path/to/lineage/data")
    usage = get_storage_usage(storage_path)

    # Check storage capacity
    if usage["percent_used"] > 80:
        print("Storage capacity warning:")
        print(f"Used: {usage['used_mb']:.1f} MB")
        print(f"Free: {usage['free_mb']:.1f} MB")
    ```
"""

import logging
from pathlib import Path
from typing import Dict

import psutil

logger = logging.getLogger(__name__)


def get_storage_usage(storage_path: Path) -> Dict[str, float]:
    """
    Get storage usage information for the lineage data directory.

    This function calculates disk space usage metrics for the specified
    storage directory, including total space, used space, free space,
    and usage percentage.

    Args:
        storage_path: Path to the storage directory

    Returns:
        Dictionary containing storage usage metrics:
            - total_mb: Total storage space in megabytes
            - used_mb: Used storage space in megabytes
            - free_mb: Available storage space in megabytes
            - percent_used: Percentage of storage space used

    Example:
        ```python
        # Get storage metrics
        storage_path = Path("/data/lineage")
        usage = get_storage_usage(storage_path)

        # Monitor storage capacity
        if usage["percent_used"] > 90:
            print("Storage capacity critical!")
            print(f"Total: {usage['total_mb']:.1f} MB")
            print(f"Used: {usage['used_mb']:.1f} MB")
            print(f"Free: {usage['free_mb']:.1f} MB")
            print(f"Usage: {usage['percent_used']:.1f}%")
        ```
    """
    if not storage_path.exists():
        return {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent_used": 0}

    try:
        usage = psutil.disk_usage(str(storage_path.parent))
        return {
            "total_mb": usage.total / (1024 * 1024),
            "used_mb": usage.used / (1024 * 1024),
            "free_mb": usage.free / (1024 * 1024),
            "percent_used": usage.percent,
        }
    except Exception as e:
        logger.error(f"Error getting storage usage: {e}")
        return {"total_mb": 0, "used_mb": 0, "free_mb": 0, "percent_used": 0}
