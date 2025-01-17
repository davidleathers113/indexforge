"""Status monitoring and management functionality.

This module provides the StatusManager class for monitoring real-time status
of document processing operations and system metrics.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil

from src.core.monitoring.status.models.status import StatusMetrics, SystemStatus, SystemStatusReport
from src.core.processing.steps.models.step import ProcessingStatus

logger = logging.getLogger(__name__)


class StatusManager:
    """Manages real-time status monitoring and metrics collection.

    This class provides functionality for tracking document processing status,
    system metrics, and overall health indicators.

    Example:
        ```python
        manager = StatusManager(storage_backend)

        # Get current system status
        status = manager.get_current_status()
        print(f"System status: {status.status}")
        print(f"Active documents: {status.current_metrics.active_documents}")

        # Get historical metrics
        metrics = manager.get_historical_metrics(
            start_time=datetime.now(UTC) - timedelta(hours=1)
        )
        ```
    """

    def __init__(self, storage: Any) -> None:
        """Initialize the status manager.

        Args:
            storage: Storage backend for document lineage data
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    def get_current_metrics(self) -> StatusMetrics:
        """Get current system metrics.

        Returns:
            Current StatusMetrics
        """
        lineage_data = self.storage.get_all_lineage()

        active_docs = 0
        queued_docs = 0
        completed_docs = 0
        error_count = 0
        total_processing_time = 0.0
        total_processed = 0

        for lineage in lineage_data.values():
            if not lineage.processing_steps:
                queued_docs += 1
                continue

            last_step = lineage.processing_steps[-1]

            if last_step.status in [ProcessingStatus.RUNNING, ProcessingStatus.PENDING]:
                active_docs += 1
            elif last_step.status == ProcessingStatus.SUCCESS:
                completed_docs += 1
                if last_step.duration_ms:
                    total_processing_time += last_step.duration_ms
                    total_processed += 1
            elif last_step.status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                error_count += 1
                completed_docs += 1

        # Calculate success rate and average processing time
        total_docs = completed_docs + active_docs + queued_docs
        success_rate = (completed_docs - error_count) / total_docs * 100 if total_docs > 0 else 0
        avg_processing_time = (
            total_processing_time / total_processed if total_processed > 0 else None
        )

        # Get system metrics
        try:
            system_load = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
        except Exception as e:
            self.logger.warning("Failed to get system metrics: %s", str(e))
            system_load = None
            memory_usage = None

        return StatusMetrics(
            active_documents=active_docs,
            queued_documents=queued_docs,
            completed_documents=completed_docs,
            error_count=error_count,
            success_rate=success_rate,
            average_processing_time=avg_processing_time,
            system_load=system_load,
            memory_usage=memory_usage,
        )

    def get_historical_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get historical performance metrics.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary of historical metrics
        """
        lineage_data = self.storage.get_all_lineage()
        metrics: Dict[str, List[float]] = {
            "success_rates": [],
            "processing_times": [],
            "error_rates": [],
        }

        # Default to last 24 hours if no time range specified
        if not start_time:
            start_time = datetime.now(UTC) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(UTC)

        # Group metrics by hour
        current_hour = start_time
        while current_hour < end_time:
            next_hour = current_hour + timedelta(hours=1)

            success_count = 0
            error_count = 0
            total_time = 0.0
            total_docs = 0

            for lineage in lineage_data.values():
                for step in lineage.processing_steps:
                    if current_hour <= step.timestamp < next_hour:
                        if step.status == ProcessingStatus.SUCCESS:
                            success_count += 1
                            if step.duration_ms:
                                total_time += step.duration_ms
                                total_docs += 1
                        elif step.status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                            error_count += 1

            total = success_count + error_count
            if total > 0:
                metrics["success_rates"].append(success_count / total * 100)
                metrics["error_rates"].append(error_count / total * 100)
            if total_docs > 0:
                metrics["processing_times"].append(total_time / total_docs)

            current_hour = next_hour

        return metrics

    def get_current_status(self) -> SystemStatusReport:
        """Get current system status report.

        Returns:
            Current SystemStatusReport
        """
        current_metrics = self.get_current_metrics()
        historical_metrics = self.get_historical_metrics(
            start_time=datetime.now(UTC) - timedelta(hours=1)
        )

        # Determine system status based on metrics
        warnings = []
        errors = []

        # Check system metrics
        if current_metrics.system_load and current_metrics.system_load > 80:
            warnings.append(f"High CPU usage: {current_metrics.system_load}%")
        if current_metrics.memory_usage and current_metrics.memory_usage > 80:
            warnings.append(f"High memory usage: {current_metrics.memory_usage}%")

        # Check processing metrics
        if current_metrics.success_rate < 90:
            warnings.append(f"Low success rate: {current_metrics.success_rate:.1f}%")
        if current_metrics.error_count > 10:
            errors.append(f"High error count: {current_metrics.error_count}")

        # Determine overall status
        if errors:
            status = SystemStatus.CRITICAL
        elif warnings:
            status = SystemStatus.DEGRADED
        else:
            status = SystemStatus.HEALTHY

        return SystemStatusReport(
            status=status,
            current_metrics=current_metrics,
            historical_metrics=historical_metrics,
            warnings=warnings,
            errors=errors,
        )

    def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get status information for a specific document.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary containing document status information

        Raises:
            ValueError: If document not found
        """
        lineage = self.storage.get_lineage(doc_id)
        if not lineage:
            raise ValueError(f"Document {doc_id} not found")

        status_info = {
            "doc_id": doc_id,
            "processing_steps": [],
            "current_status": None,
            "error_count": 0,
            "total_processing_time": 0.0,
            "start_time": None,
            "last_updated": None,
        }

        if not lineage.processing_steps:
            status_info["current_status"] = "PENDING"
            return status_info

        # Analyze processing steps
        for step in lineage.processing_steps:
            step_info = {
                "step_name": step.step_name,
                "status": step.status.value,
                "timestamp": step.timestamp.isoformat(),
                "duration_ms": step.duration_ms,
                "error_message": step.error_message,
            }
            status_info["processing_steps"].append(step_info)

            if step.status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                status_info["error_count"] += 1
            if step.duration_ms:
                status_info["total_processing_time"] += step.duration_ms

        # Set timing information
        status_info["start_time"] = lineage.processing_steps[0].timestamp.isoformat()
        status_info["last_updated"] = lineage.processing_steps[-1].timestamp.isoformat()
        status_info["current_status"] = lineage.processing_steps[-1].status.value

        return status_info
