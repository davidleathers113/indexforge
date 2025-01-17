"""Health check lifecycle management.

This module provides the HealthCheckManager class for monitoring system health,
including resource usage and document processing metrics.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import psutil

from src.core.monitoring.errors.models.log_entry import LogLevel
from src.core.monitoring.health.models.status import (
    HealthCheckResult,
    HealthStatus,
    ResourceMetrics,
)

logger = logging.getLogger(__name__)


class HealthCheckManager:
    """Manages system health monitoring and status tracking.

    This class handles system health checks, resource monitoring, and document
    processing metrics collection.

    Example:
        ```python
        manager = HealthCheckManager(
            storage_instance,
            thresholds={
                "memory_critical": 90.0,
                "memory_warning": 80.0,
                "cpu_critical": 90.0,
                "cpu_warning": 80.0,
            }
        )

        # Perform health check
        result = manager.perform_health_check()
        if result.status != HealthStatus.HEALTHY:
            for issue in result.issues:
                print(f"Health issue: {issue}")
        ```

    Attributes:
        storage: Storage backend for accessing document data
        thresholds: Health check thresholds
    """

    def __init__(
        self,
        storage: Any,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize the health check manager.

        Args:
            storage: Storage backend instance
            thresholds: Optional custom thresholds for health checks
        """
        self.storage = storage
        self.thresholds = thresholds or {}

    def get_resource_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics.

        Returns:
            ResourceMetrics instance with current usage data
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        virtual_memory = psutil.virtual_memory()

        return ResourceMetrics(
            memory_total=memory_info.rss // (1024 * 1024),  # Convert to MB
            memory_available=virtual_memory.available // (1024 * 1024),  # Convert to MB
            memory_percent=process.memory_percent(),
            cpu_percent=process.cpu_percent(interval=1.0),
            timestamp=datetime.now(UTC),
        )

    def perform_health_check(self) -> HealthCheckResult:
        """Perform a comprehensive system health check.

        This method checks:
        - System resource usage (memory, CPU)
        - Document processing metrics
        - Error and warning rates
        - Processing time statistics

        Returns:
            HealthCheckResult containing status and metrics

        Example:
            ```python
            result = manager.perform_health_check()
            print(f"System status: {result.status.value}")
            print(f"Memory usage: {result.metrics.memory_percent:.1f}%")
            print(f"CPU usage: {result.metrics.cpu_percent:.1f}%")
            ```
        """
        logger.debug("Starting health check...")

        # Get current resource metrics
        metrics = self.get_resource_metrics()
        issues = []
        status = HealthStatus.HEALTHY

        # Get threshold values
        memory_critical = self.thresholds.get("memory_critical", 90.0)
        memory_warning = self.thresholds.get("memory_warning", 80.0)
        cpu_critical = self.thresholds.get("cpu_critical", 90.0)
        cpu_warning = self.thresholds.get("cpu_warning", 80.0)
        error_threshold = self.thresholds.get("error_rate_critical", 0.1)
        warning_threshold = self.thresholds.get("error_rate_warning", 0.05)

        # Check resource usage
        if metrics.memory_percent >= memory_critical:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Memory usage critical: {metrics.memory_percent:.1f}%")
            logger.warning(
                "Critical memory usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": metrics.memory_percent, "threshold": memory_critical},
            )
        elif metrics.memory_percent >= memory_warning:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"Memory usage warning: {metrics.memory_percent:.1f}%")
            logger.warning(
                "High memory usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": metrics.memory_percent, "threshold": memory_warning},
            )

        if metrics.cpu_percent >= cpu_critical:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Critical CPU usage: {metrics.cpu_percent:.1f}%")
            logger.warning(
                "Critical CPU usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": metrics.cpu_percent, "threshold": cpu_critical},
            )
        elif metrics.cpu_percent >= cpu_warning:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            logger.warning(
                "High CPU usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": metrics.cpu_percent, "threshold": cpu_warning},
            )

        try:
            # Check document processing metrics
            lineage_data = self.storage.get_all_lineage()
            total_docs = len(lineage_data)
            error_count = 0
            warning_count = 0
            failed_docs = 0
            total_processing_time = 0.0
            docs_with_time = 0

            for doc_id, lineage in lineage_data.items():
                # Check for errors and warnings
                for log in lineage.error_logs:
                    try:
                        if isinstance(log, dict):
                            log_level = LogLevel(log.get("level", "ERROR"))
                        else:
                            log_level = log.log_level

                        if log_level == LogLevel.ERROR:
                            error_count += 1
                        elif log_level == LogLevel.WARNING:
                            warning_count += 1
                    except (ValueError, AttributeError) as e:
                        logger.error(f"Error processing log entry for document {doc_id}: {e}")
                        error_count += 1

                # Check processing status and time
                if lineage.processing_steps:
                    last_step = lineage.processing_steps[-1]
                    if getattr(last_step, "status", "ERROR") in ["ERROR", "FAILED"]:
                        failed_docs += 1

                    # Calculate processing time
                    if len(lineage.processing_steps) > 1:
                        try:
                            first_step = lineage.processing_steps[0]
                            if isinstance(first_step, dict):
                                start_time = datetime.fromisoformat(first_step["timestamp"])
                                end_time = datetime.fromisoformat(last_step["timestamp"])
                            else:
                                start_time = first_step.timestamp
                                end_time = last_step.timestamp
                            processing_time = (end_time - start_time).total_seconds()
                            total_processing_time += processing_time
                            docs_with_time += 1
                        except (ValueError, AttributeError, KeyError) as e:
                            logger.error(
                                f"Error calculating processing time for document {doc_id}: {e}"
                            )

            # Calculate rates
            error_rate = error_count / max(total_docs, 1)
            warning_rate = warning_count / max(total_docs, 1)
            failed_docs_ratio = failed_docs / max(total_docs, 1)
            avg_processing_time = total_processing_time / max(docs_with_time, 1)

            # Update status based on error rates
            if error_rate >= error_threshold:
                status = max(status, HealthStatus.CRITICAL)
                issues.append(f"High error rate: {error_rate:.1%}")
            elif warning_rate >= warning_threshold:
                status = max(status, HealthStatus.WARNING)
                issues.append(f"Elevated warning rate: {warning_rate:.1%}")

            return HealthCheckResult(
                status=status,
                metrics=metrics,
                issues=issues,
                error_rate=error_rate,
                warning_rate=warning_rate,
                failed_docs_ratio=failed_docs_ratio,
                avg_processing_time=avg_processing_time,
                total_docs=total_docs,
            )

        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return HealthCheckResult(
                status=HealthStatus.CRITICAL,
                metrics=metrics,
                issues=[f"Health check failed: {str(e)}"],
            )
