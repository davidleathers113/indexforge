"""Metrics collection and aggregation for document processing."""

from datetime import UTC, datetime
import logging
from typing import TYPE_CHECKING, Any, Union

from .enums import LogLevel, ProcessingStatus
from .models import DocumentLineage, ProcessingStep


if TYPE_CHECKING:
    from .storage import LineageStorage

logger = logging.getLogger(__name__)


def normalize_datetime(dt: datetime | None) -> datetime | None:
    """Ensure datetime is timezone-aware (UTC).

    Args:
        dt: Datetime to normalize

    Returns:
        Timezone-aware datetime in UTC
    """
    if dt is None:
        return None
    try:
        if dt.tzinfo is None:
            logger.debug("Converting naive datetime to UTC: %s", dt)
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (AttributeError, ValueError) as e:
        logger.error("Failed to normalize datetime %s: %s", dt, str(e))
        raise ValueError(f"Invalid datetime value: {dt}") from e


def get_latest_processing_step(doc_id: str, lineage: DocumentLineage) -> ProcessingStep | None:
    """Get the most recent processing step for a document.

    Args:
        doc_id: ID of the document
        lineage: Document lineage data

    Returns:
        Most recent ProcessingStep or None if no steps exist
    """
    try:
        steps = lineage.processing_steps
        if not steps:
            logger.debug("No processing steps found for document %s", doc_id)
            return None
        logger.debug("Found %d processing steps for document %s", len(steps), doc_id)
        return steps[-1]
    except (AttributeError, IndexError) as e:
        logger.error("Error getting latest processing step for document %s: %s", doc_id, str(e))
        return None


def get_aggregated_metrics(
    lineage_data: dict[str, DocumentLineage],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict[str, Any]:
    """Get aggregated metrics across all documents.

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data
        start_time: Optional start time for filtering metrics
        end_time: Optional end time for filtering metrics

    Returns:
        Dictionary containing aggregated metrics
    """
    logger.info(
        "Calculating aggregated metrics for %d documents (time range: %s to %s)",
        len(lineage_data),
        start_time,
        end_time,
    )

    # Normalize input datetimes
    try:
        start_time = normalize_datetime(start_time)
        end_time = normalize_datetime(end_time)
    except ValueError as e:
        logger.error("Failed to normalize time range: %s", str(e))
        raise

    metrics = {
        "document_count": len(lineage_data),
        "processing": {
            "total_time": 0.0,
            "average_time": 0.0,
            "completed_docs": 0,
            "in_progress_docs": 0,
            "failed_docs": 0,
            "pending_docs": 0,  # Added for test compatibility
        },
        "errors": {
            "total_errors": 0,
            "total_warnings": 0,
            "error_rate": 0.0,
            "warning_rate": 0.0,
        },
        "resources": {
            "peak_memory_mb": 0,
            "total_cpu_time": 0.0,
            "average_memory_mb": 0.0,
        },
        "time_range": {
            "start": None,
            "end": None,
        },
    }

    if not lineage_data:
        logger.info("No documents to process")
        return metrics

    # Track document processing status and times
    processing_times = []
    memory_usages = []
    error_count = 0
    warning_count = 0
    processed_docs = 0

    for doc_id, lineage in lineage_data.items():
        try:
            # Get the latest step for time filtering
            latest_step = get_latest_processing_step(doc_id, lineage)
            if not latest_step:
                # Document has no processing steps, mark as pending
                metrics["processing"]["pending_docs"] += 1
                logger.debug("Document %s is pending (no processing steps)", doc_id)
                # Use document creation time for time range
                doc_time = normalize_datetime(lineage.created_at)
                if start_time and doc_time < start_time:
                    continue
                if end_time and doc_time > end_time:
                    continue
                processed_docs += 1
                if (
                    metrics["time_range"]["start"] is None
                    or doc_time < metrics["time_range"]["start"]
                ):
                    metrics["time_range"]["start"] = doc_time
                if metrics["time_range"]["end"] is None or doc_time > metrics["time_range"]["end"]:
                    metrics["time_range"]["end"] = doc_time
                continue

            # Filter by time range if specified
            step_time = normalize_datetime(latest_step.timestamp)
            if start_time and step_time < start_time:
                logger.debug("Skipping document %s: before start time", doc_id)
                continue
            if end_time and step_time > end_time:
                logger.debug("Skipping document %s: after end time", doc_id)
                continue

            processed_docs += 1

            # Update time range
            if metrics["time_range"]["start"] is None or step_time < metrics["time_range"]["start"]:
                metrics["time_range"]["start"] = step_time
            if metrics["time_range"]["end"] is None or step_time > metrics["time_range"]["end"]:
                metrics["time_range"]["end"] = step_time

            # Process performance metrics from step details
            for step in lineage.processing_steps:
                # Skip steps outside the time range
                step_time = normalize_datetime(step.timestamp)
                if start_time and step_time < start_time:
                    continue
                if end_time and step_time > end_time:
                    continue

                if step.details and "metrics" in step.details:
                    step_metrics = step.details["metrics"]
                    if "processing_time" in step_metrics:
                        processing_times.append(step_metrics["processing_time"])
                        logger.debug(
                            "Document %s processing time: %.2fs",
                            doc_id,
                            step_metrics["processing_time"],
                        )
                    if "memory_usage" in step_metrics:
                        memory_usages.append(step_metrics["memory_usage"])
                        logger.debug(
                            "Document %s memory usage: %d MB",
                            doc_id,
                            step_metrics["memory_usage"],
                        )

            # Count errors and warnings
            for log_entry in lineage.error_logs:
                try:
                    # Skip logs outside the time range
                    log_time = normalize_datetime(log_entry.timestamp)
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        continue

                    if hasattr(log_entry, "log_level"):
                        log_level = LogLevel(log_entry.log_level)
                    else:
                        log_level = LogLevel(log_entry.get("log_level", "error"))

                    if log_level == LogLevel.ERROR:
                        error_count += 1
                        logger.debug("Found error in document %s: %s", doc_id, log_entry.message)
                    elif log_level == LogLevel.WARNING:
                        warning_count += 1
                        logger.debug("Found warning in document %s: %s", doc_id, log_entry.message)
                except (AttributeError, ValueError) as e:
                    logger.error("Invalid log entry format in document %s: %s", doc_id, str(e))

            # Track document status
            if latest_step.status == ProcessingStatus.SUCCESS:
                metrics["processing"]["completed_docs"] += 1
                logger.debug("Document %s completed successfully", doc_id)
            elif latest_step.status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                metrics["processing"]["failed_docs"] += 1
                logger.debug("Document %s failed processing", doc_id)
            elif latest_step.status in [ProcessingStatus.IN_PROGRESS, ProcessingStatus.RUNNING]:
                metrics["processing"]["in_progress_docs"] += 1
                logger.debug("Document %s is in progress", doc_id)

        except Exception as e:
            logger.error(
                "Error processing metrics for document %s: %s",
                doc_id,
                str(e),
                exc_info=True,
            )
            continue

    # Calculate aggregated metrics
    try:
        if processing_times:
            metrics["processing"]["total_time"] = sum(processing_times)
            metrics["processing"]["average_time"] = sum(processing_times) / len(processing_times)
            logger.debug(
                "Average processing time: %.2fs (total: %.2fs)",
                metrics["processing"]["average_time"],
                metrics["processing"]["total_time"],
            )

        if memory_usages:
            metrics["resources"]["peak_memory_mb"] = max(memory_usages)
            metrics["resources"]["average_memory_mb"] = sum(memory_usages) / len(memory_usages)
            logger.debug(
                "Peak memory usage: %d MB (average: %.2f MB)",
                metrics["resources"]["peak_memory_mb"],
                metrics["resources"]["average_memory_mb"],
            )

        total_docs = max(processed_docs, 1)  # Avoid division by zero
        metrics["errors"]["total_errors"] = error_count
        metrics["errors"]["total_warnings"] = warning_count
        metrics["errors"]["error_rate"] = round(
            error_count / total_docs, 2
        )  # Round to 2 decimal places
        metrics["errors"]["warning_rate"] = round(
            warning_count / total_docs, 2
        )  # Round to 2 decimal places

        logger.info(
            "Metrics calculation complete - Processed: %d, Completed: %d, Failed: %d, In Progress: %d, Pending: %d",
            processed_docs,
            metrics["processing"]["completed_docs"],
            metrics["processing"]["failed_docs"],
            metrics["processing"]["in_progress_docs"],
            metrics["processing"]["pending_docs"],
        )
        logger.info(
            "Error statistics - Errors: %d (%.1f%%), Warnings: %d (%.1f%%)",
            error_count,
            metrics["errors"]["error_rate"] * 100,
            warning_count,
            metrics["errors"]["warning_rate"] * 100,
        )

    except Exception as e:
        logger.error("Error calculating final metrics: %s", str(e), exc_info=True)
        raise

    return metrics


def update_performance_metrics(
    lineage: DocumentLineage,
    metric_name: str,
    value: float | int | dict,
    operation: str = "set",
) -> None:
    """Update performance metrics for a document.

    Args:
        lineage: Document lineage data
        metric_name: Name of the metric to update
        value: New value for the metric
        operation: Type of update operation ('set' or 'increment')

    Raises:
        ValueError: If operation is invalid
    """
    if operation not in ["set", "increment"]:
        logger.error("Invalid operation: %s", operation)
        raise ValueError("Operation must be either 'set' or 'increment'")

    try:
        current_value = lineage.performance_metrics.get(metric_name, 0)

        if operation == "set":
            lineage.performance_metrics[metric_name] = value
            logger.debug("Set metric %s = %s", metric_name, value)
        elif operation == "increment":
            if not isinstance(current_value, (int, float)) or not isinstance(value, (int, float)):
                logger.error(
                    "Invalid value types for increment: current=%s, new=%s",
                    type(current_value),
                    type(value),
                )
                raise ValueError("Increment operation only supported for numeric values")
            lineage.performance_metrics[metric_name] = current_value + value
            logger.debug(
                "Incremented metric %s: %s + %s = %s",
                metric_name,
                current_value,
                value,
                lineage.performance_metrics[metric_name],
            )

        lineage.last_modified = datetime.now(UTC)

    except Exception as e:
        logger.error(
            "Error updating metric %s: %s",
            metric_name,
            str(e),
            exc_info=True,
        )
        raise


def get_real_time_status(
    storage_or_lineage: Union["LineageStorage", dict[str, DocumentLineage]],
    doc_id: str | None = None,
) -> dict[str, Any]:
    """Get real-time status of document processing.

    Args:
        storage_or_lineage: Storage instance or dictionary of lineage data
        doc_id: Optional document ID to get status for specific document

    Returns:
        Dictionary containing real-time status metrics
    """
    from .storage import LineageStorage  # Import here to avoid circular import

    logger.info("Getting real-time status%s", f" for document {doc_id}" if doc_id else "")

    try:
        if isinstance(storage_or_lineage, LineageStorage):
            if doc_id:
                lineage = storage_or_lineage.get_lineage(doc_id)
                if not lineage:
                    logger.error("Document %s not found", doc_id)
                    raise ValueError(f"Document {doc_id} not found")
                lineage_data = {doc_id: lineage}
            else:
                lineage_data = storage_or_lineage.get_all_lineage()
        else:
            lineage_data = storage_or_lineage

        now = datetime.now(UTC)
        active_docs = 0
        queued_docs = 0
        processing_docs = 0
        completed_docs = 0
        total_success = 0
        total_errors = 0
        processing_times = []
        current_step = None
        current_status = None

        for doc_id, lineage in lineage_data.items():
            if not lineage.processing_steps:
                queued_docs += 1
                logger.debug("Document %s is queued", doc_id)
                continue

            last_step = lineage.processing_steps[-1]
            current_step = last_step.step_name
            current_status = last_step.status

            # Count completed steps for this document
            completed_steps = sum(
                1
                for step in lineage.processing_steps[:-1]
                if step.status == ProcessingStatus.SUCCESS
            )
            if completed_steps > 0:
                completed_docs += 1

            if last_step.status in [ProcessingStatus.IN_PROGRESS, ProcessingStatus.RUNNING]:
                active_docs += 1
                processing_docs += 1
                logger.debug("Document %s is active (%s)", doc_id, last_step.step_name)
            elif last_step.status == ProcessingStatus.SUCCESS:
                total_success += 1
                completed_docs += 1
                logger.debug("Document %s completed successfully", doc_id)
            elif last_step.status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]:
                total_errors += 1
                completed_docs += 1
                logger.debug("Document %s failed", doc_id)

            # Calculate processing time if we have multiple steps
            if len(lineage.processing_steps) > 1:
                try:
                    start_time = normalize_datetime(lineage.processing_steps[0].timestamp)
                    end_time = normalize_datetime(last_step.timestamp)
                    processing_time = (end_time - start_time).total_seconds()
                    processing_times.append(processing_time)
                    logger.debug(
                        "Document %s processing time: %.2fs",
                        doc_id,
                        processing_time,
                    )
                except (AttributeError, ValueError) as e:
                    logger.error(
                        "Error calculating processing time for document %s: %s",
                        doc_id,
                        str(e),
                    )

        total_steps = total_errors + total_success
        error_rate = (total_errors / total_steps * 100) if total_steps > 0 else 0
        success_rate = (total_success / total_steps * 100) if total_steps > 0 else 0
        avg_processing_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0
        )

        status = {
            "active_documents": active_docs,
            "active_processes": active_docs,  # For backward compatibility
            "queued_documents": queued_docs,
            "processing_documents": processing_docs,
            "completed_documents": completed_docs,
            "error_rate": error_rate,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "last_update": now.isoformat(),
            "current_step": current_step,
            "status": current_status,
        }

        logger.info(
            "Status - Active: %d, Queued: %d, Processing: %d, Completed: %d",
            active_docs,
            queued_docs,
            processing_docs,
            completed_docs,
        )
        logger.info(
            "Performance - Success Rate: %.1f%%, Error Rate: %.1f%%, Avg Time: %.2fs",
            success_rate,
            error_rate,
            avg_processing_time,
        )

        return status

    except Exception as e:
        logger.error("Error getting real-time status: %s", str(e), exc_info=True)
        raise
