"""
System health check logic for document lineage tracking.

This module contains methods for:
- Performing system health checks
- Calculating health statuses based on metrics and resource usage
"""

from datetime import datetime, timezone
import logging
import os
from typing import Dict, Optional

import psutil

from .enums import HealthStatus, LogLevel, ProcessingStatus
from .models import HealthCheckResult
from .storage import LineageStorage

logger = logging.getLogger(__name__)


def calculate_health_status(
    storage: "LineageStorage",
    memory_info: Optional[Dict[str, int]] = None,
    cpu_percent: Optional[float] = None,
    memory_percent: Optional[float] = None,
    error_threshold: float = 0.1,
    warning_threshold: float = 0.05,
    memory_critical: float = 90.0,
    memory_warning: float = 80.0,
    cpu_critical: float = 90.0,
    cpu_warning: float = 80.0,
    processing_time_critical: float = 600.0,
    processing_time_warning: float = 300.0,
    thresholds: Optional[Dict[str, float]] = None,
) -> HealthCheckResult:
    """Calculate detailed health status based on metrics and resource usage.

    Args:
        storage: Storage instance to check
        memory_info: Optional dictionary with memory info (total, available in MB)
        cpu_percent: Optional CPU usage percentage
        memory_percent: Optional memory usage percentage
        error_threshold: Critical error rate threshold
        warning_threshold: Warning error rate threshold
        memory_critical: Critical memory usage threshold
        memory_warning: Warning memory usage threshold
        cpu_critical: Critical CPU usage threshold
        cpu_warning: Warning CPU usage threshold
        processing_time_critical: Critical processing time threshold
        processing_time_warning: Warning processing time threshold
        thresholds: Optional custom thresholds for health checks

    Returns:
        HealthCheckResult object containing status and details
    """
    logger.debug("Starting detailed health status calculation...")

    # Initialize metrics
    error_count = 0
    warning_count = 0
    failed_docs = 0
    total_docs = 0
    avg_processing_time = 0.0

    # Get resource metrics if not provided
    if memory_info is None or cpu_percent is None or memory_percent is None:
        process = psutil.Process(os.getpid())
        if memory_info is None:
            memory_info = {
                "total": process.memory_info().rss // (1024 * 1024),  # Convert to MB
                "available": psutil.virtual_memory().available // (1024 * 1024),  # Convert to MB
            }
            logger.debug(f"Using current process memory info: {memory_info}")
        if memory_percent is None:
            memory_percent = process.memory_percent()
            logger.debug(f"Using current process memory percentage: {memory_percent:.1f}%")
        if cpu_percent is None:
            cpu_percent = process.cpu_percent(interval=1.0)
            logger.debug(f"Using current process CPU percentage: {cpu_percent:.1f}%")

    # Apply custom thresholds if provided
    if thresholds:
        logger.debug(f"Applying custom thresholds: {thresholds}")
        memory_critical = thresholds.get("memory_critical", memory_critical)
        memory_warning = thresholds.get("memory_warning", memory_warning)
        cpu_critical = thresholds.get("cpu_critical", cpu_critical)
        cpu_warning = thresholds.get("cpu_warning", cpu_warning)
        error_threshold = thresholds.get("error_rate_critical", error_threshold)
        warning_threshold = thresholds.get("error_rate_warning", warning_threshold)
        processing_time_critical = thresholds.get(
            "processing_time_critical", processing_time_critical
        )
        processing_time_warning = thresholds.get("processing_time_warning", processing_time_warning)

    logger.debug(
        "Current metrics - Memory: %(memory)s MB (%(memory_pct).1f%%), CPU: %(cpu).1f%%, Available Memory: %(avail)s MB",
        {
            "memory": memory_info["total"],
            "memory_pct": memory_percent,
            "cpu": cpu_percent,
            "avail": memory_info["available"],
        },
    )
    logger.debug(
        "Thresholds - Memory: %(mem_warn).1f%%/%(mem_crit).1f%%, CPU: %(cpu_warn).1f%%/%(cpu_crit).1f%%, Errors: %(err_warn).1f%%/%(err_crit).1f%%",
        {
            "mem_warn": memory_warning,
            "mem_crit": memory_critical,
            "cpu_warn": cpu_warning,
            "cpu_crit": cpu_critical,
            "err_warn": warning_threshold * 100,
            "err_crit": error_threshold * 100,
        },
    )

    issues = []
    status = HealthStatus.HEALTHY
    now = datetime.now(timezone.utc)

    try:
        # Check resource usage
        if memory_percent >= memory_critical:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Memory usage critical: {memory_percent:.1f}%")
            logger.warning(
                "Critical memory usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": memory_percent, "threshold": memory_critical},
            )
        elif memory_percent >= memory_warning:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"Memory usage warning: {memory_percent:.1f}%")
            logger.warning(
                "High memory usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": memory_percent, "threshold": memory_warning},
            )

        if cpu_percent >= cpu_critical:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            logger.warning(
                "Critical CPU usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": cpu_percent, "threshold": cpu_critical},
            )
        elif cpu_percent >= cpu_warning:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            logger.warning(
                "High CPU usage: %(current).1f%% >= %(threshold).1f%%",
                {"current": cpu_percent, "threshold": cpu_warning},
            )

        # Check document processing status
        lineage_data = storage.get_all_lineage()
        total_docs = len(lineage_data)
        logger.debug(f"Processing {total_docs} documents")

        total_processing_time = 0.0
        docs_with_time = 0

        for doc_id, lineage in lineage_data.items():
            # Check for errors and warnings
            for log in lineage.error_logs:
                try:
                    if isinstance(log, dict):
                        log_level = LogLevel(log.get("log_level", "error").lower())
                    else:
                        log_level = log.log_level

                    if log_level == LogLevel.ERROR:
                        error_count += 1
                        logger.debug(f"Found error in document {doc_id}: {log}")
                    elif log_level == LogLevel.WARNING:
                        warning_count += 1
                        logger.debug(f"Found warning in document {doc_id}: {log}")
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing log entry for document {doc_id}: {e}")
                    error_count += 1

            # Check processing status
            if lineage.processing_steps:
                last_step = lineage.processing_steps[-1]
                try:
                    if isinstance(last_step, dict):
                        status_value = last_step.get("status", "error").lower()
                        step_status = ProcessingStatus(status_value)
                    else:
                        step_status = last_step.status

                    if step_status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                        failed_docs += 1
                        logger.debug(f"Document {doc_id} failed processing: {last_step}")
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing step status for document {doc_id}: {e}")
                    failed_docs += 1

                # Calculate processing time if we have multiple steps
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
                        logger.debug(f"Document {doc_id} processing time: {processing_time:.1f}s")
                    except (ValueError, AttributeError, KeyError) as e:
                        logger.error(
                            f"Error calculating processing time for document {doc_id}: {e}"
                        )

        # Calculate error and warning rates
        error_rate = error_count / max(total_docs, 1)
        warning_rate = warning_count / max(total_docs, 1)
        failed_ratio = failed_docs / max(total_docs, 1)
        avg_processing_time = total_processing_time / max(docs_with_time, 1)

        logger.debug(
            "Document metrics - Errors: %(errors)d (%(error_rate).1f%%), Warnings: %(warnings)d (%(warning_rate).1f%%), Failed: %(failed)d (%(failed_rate).1f%%)",
            {
                "errors": error_count,
                "error_rate": error_rate * 100,
                "warnings": warning_count,
                "warning_rate": warning_rate * 100,
                "failed": failed_docs,
                "failed_rate": failed_ratio * 100,
            },
        )

        # Update status based on error and warning rates
        if error_count > 0:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"Found {error_count} document error(s)")
            logger.warning(
                "Document errors found: %(count)d error(s)",
                {"count": error_count},
            )
        elif warning_count > 0:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"Found {warning_count} document warning(s)")
            logger.warning(
                "Document warnings found: %(count)d warning(s)",
                {"count": warning_count},
            )

        if failed_ratio >= error_threshold:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Critical failure rate: {failed_ratio:.1%}")
            logger.warning(
                "Critical failure rate: %(current).1f%% >= %(threshold).1f%%",
                {"current": failed_ratio * 100, "threshold": error_threshold * 100},
            )
        elif failed_ratio >= warning_threshold:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"High failure rate: {failed_ratio:.1%}")
            logger.warning(
                "High failure rate: %(current).1f%% >= %(threshold).1f%%",
                {"current": failed_ratio * 100, "threshold": warning_threshold * 100},
            )

        if avg_processing_time >= processing_time_critical:
            status = max(status, HealthStatus.CRITICAL)
            issues.append(f"Critical processing time: {avg_processing_time:.1f}s")
            logger.warning(
                "Critical processing time: %(current).1fs >= %(threshold).1fs",
                {"current": avg_processing_time, "threshold": processing_time_critical},
            )
        elif avg_processing_time >= processing_time_warning:
            status = max(status, HealthStatus.WARNING)
            issues.append(f"High processing time: {avg_processing_time:.1f}s")
            logger.warning(
                "High processing time: %(current).1fs >= %(threshold).1fs",
                {"current": avg_processing_time, "threshold": processing_time_warning},
            )

    except Exception as e:
        logger.error(
            "Error during health status calculation: %(error)s",
            {"error": str(e)},
            exc_info=True,
        )
        status = HealthStatus.CRITICAL
        issues.append(f"Error calculating health status: {str(e)}")

    logger.info(
        "Health check complete - Status: %(status)s, Issues: %(issues)s",
        {"status": status.value, "issues": issues},
    )

    return HealthCheckResult(
        status=status,
        issues=issues,
        timestamp=now,
        metrics={
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "total_memory_mb": memory_info["total"],
            "available_memory_mb": memory_info["available"],
            "error_count": error_count,
            "warning_count": warning_count,
            "failed_docs": failed_docs,
            "total_docs": total_docs,
            "avg_processing_time": avg_processing_time,
        },
        resources={
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
        },
    )


def perform_health_check(
    storage: "LineageStorage",
    thresholds: Optional[Dict[str, float]] = None,
) -> HealthCheckResult:
    """Perform a health check of the system.

    Args:
        storage: Storage instance to check
        thresholds: Optional custom thresholds for health checks

    Returns:
        HealthCheckResult object containing status and metrics
    """
    logger.info("Starting health check...")
    now = datetime.now(timezone.utc)

    # Get resource usage
    logger.debug("Getting resource usage...")
    process = psutil.Process(os.getpid())
    memory_info = {
        "total": process.memory_info().rss // (1024 * 1024),  # Convert to MB
        "available": psutil.virtual_memory().available // (1024 * 1024),  # Convert to MB
    }
    memory_percent = process.memory_percent()
    cpu_percent = process.cpu_percent(interval=1.0)
    logger.debug(
        f"Memory info: {memory_info}, Memory percent: {memory_percent}, CPU percent: {cpu_percent}"
    )

    # Map threshold keys to parameter names
    threshold_mapping = {
        "error_rate_critical": "error_threshold",
        "error_rate_warning": "warning_threshold",
        "memory_critical": "memory_critical",
        "memory_warning": "memory_warning",
        "cpu_critical": "cpu_critical",
        "cpu_warning": "cpu_warning",
        "processing_time_critical": "processing_time_critical",
        "processing_time_warning": "processing_time_warning",
    }

    # Convert threshold keys to parameter names
    if thresholds:
        mapped_thresholds = {
            threshold_mapping.get(key, key): value
            for key, value in thresholds.items()
            if key in threshold_mapping
        }
    else:
        mapped_thresholds = {}

    # Calculate health status
    logger.debug("Calculating detailed health status...")
    status, issues = calculate_health_status(
        storage=storage,
        memory_info=memory_info,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        **mapped_thresholds,
    )
    logger.info(f"Health check complete. Status: {status}, Issues: {issues}")

    return HealthCheckResult(
        status=status,
        issues=issues,
        timestamp=now,
        metrics={
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "total_memory_mb": memory_info["total"],
            "available_memory_mb": memory_info["available"],
        },
        resources={
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
        },
    )
