"""Real-time status and monitoring functionality for document processing.

This module provides functionality for monitoring the real-time status of
document processing operations, tracking active processes, and gathering
system metrics. It supports monitoring of processing states, system load,
and operational metrics.

Key Features:
    - Real-time status monitoring
    - Active process tracking 
    - Processing step analysis
    - System load monitoring
    - Performance metrics
    - Status aggregation

Example:
    ```python
    from datetime import datetime, timedelta
    from src.core.processing.steps.models.step import ProcessingStatus, ProcessingStep
    from src.core.models.lineage import DocumentLineage
    
    # Initialize status manager
    status_manager = StatusManager()
    
    # Monitor document processing
    doc_id = "doc123"
    status = status_manager.get_document_status(doc_id)
    print(f"Document status: {status}")
    
    # Get system metrics
    metrics = status_manager.get_system_metrics()
    print(f"Active processes: {metrics['active_processes']}")
    print(f"Success rate: {metrics['success_rate']}%")
    ```
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import psutil

from src.core.models.lineage import DocumentLineage
from src.core.processing.steps.models.step import ProcessingStatus, ProcessingStep


class StatusManager:
    """Manager for real-time status monitoring and metrics."""

    def __init__(self):
        """Initialize the status manager."""
        self._last_check = datetime.now(UTC)
        self._metrics_cache: dict[str, Any] = {}
        self._cache_duration = timedelta(seconds=5)

    def get_document_status(self, doc_id: str, lineage: DocumentLineage) -> dict[str, Any]:
        """Get the current status of a document.

        Args:
            doc_id: The document ID to check.
            lineage: The document's lineage data.

        Returns:
            A dictionary containing the document's current status information.
        """
        latest_step = self._get_latest_step(lineage)

        return {
            "doc_id": doc_id,
            "current_status": latest_step.status if latest_step else None,
            "last_step": latest_step.step_name if latest_step else None,
            "last_updated": latest_step.timestamp if latest_step else None,
            "error_message": (
                latest_step.error_message if latest_step and latest_step.error_message else None
            ),
            "metrics": latest_step.metrics if latest_step else {},
        }

    def get_system_metrics(self, lineage_data: dict[str, DocumentLineage]) -> dict[str, Any]:
        """Get current system metrics and processing statistics.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data.

        Returns:
            A dictionary containing system metrics and processing statistics.
        """
        now = datetime.now(UTC)
        if self._metrics_cache and now - self._last_check < self._cache_duration:
            return self._metrics_cache

        active_count = self._count_active_processes(lineage_data)
        total_docs = len(lineage_data)

        # Calculate success/error rates
        success_count = error_count = 0
        for lineage in lineage_data.values():
            latest = self._get_latest_step(lineage)
            if latest:
                if latest.status == ProcessingStatus.SUCCESS:
                    success_count += 1
                elif latest.status == ProcessingStatus.ERROR:
                    error_count += 1

        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        metrics = {
            "timestamp": now,
            "active_processes": active_count,
            "total_documents": total_docs,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / total_docs * 100) if total_docs > 0 else 0,
            "error_rate": (error_count / total_docs * 100) if total_docs > 0 else 0,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
            },
        }

        self._metrics_cache = metrics
        self._last_check = now
        return metrics

    def get_processing_summary(
        self, lineage_data: dict[str, DocumentLineage], time_window: timedelta | None = None
    ) -> dict[str, Any]:
        """Get a summary of processing activities.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data.
            time_window: Optional time window to limit the summary. Defaults to all time.

        Returns:
            A dictionary containing processing statistics and summaries.
        """
        now = datetime.now(UTC)
        cutoff = now - time_window if time_window else None

        step_counts: dict[str, int] = {}
        status_counts: dict[ProcessingStatus, int] = {}
        total_duration = timedelta()
        processed_docs = 0

        for lineage in lineage_data.values():
            for step in lineage.processing_steps:
                if cutoff and step.timestamp < cutoff:
                    continue

                step_counts[step.step_name] = step_counts.get(step.step_name, 0) + 1
                status_counts[step.status] = status_counts.get(step.status, 0) + 1

                if step.duration:
                    total_duration += step.duration
                    processed_docs += 1

        return {
            "time_window": str(time_window) if time_window else "all",
            "total_documents": len(lineage_data),
            "processed_documents": processed_docs,
            "step_counts": step_counts,
            "status_counts": {str(k): v for k, v in status_counts.items()},
            "average_duration": (total_duration / processed_docs) if processed_docs > 0 else None,
        }

    def _get_latest_step(self, lineage: DocumentLineage) -> ProcessingStep | None:
        """Get the most recent processing step from lineage data."""
        if not lineage.processing_steps:
            return None
        return max(lineage.processing_steps, key=lambda x: x.timestamp)

    def _count_active_processes(self, lineage_data: dict[str, DocumentLineage]) -> int:
        """Count the number of currently active processing operations."""
        active_count = 0
        for lineage in lineage_data.values():
            latest = self._get_latest_step(lineage)
            if latest and latest.status == ProcessingStatus.RUNNING:
                active_count += 1
        return active_count
