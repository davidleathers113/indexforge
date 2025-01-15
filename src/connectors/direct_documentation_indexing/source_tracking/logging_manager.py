"""
Document processing logging and error tracking.

This module provides functionality for tracking and managing processing steps,
errors, and warnings during document processing. It supports filtering logs by
level, time range, and document, with utilities for aggregating recent errors
across multiple documents.

Key Features:
    - Processing step tracking
    - Error and warning logging
    - Time-based log filtering
    - Log level filtering
    - Cross-document error aggregation
    - Recent error retrieval

Example:
    ```python
    from datetime import datetime, timedelta
    from .models import DocumentLineage
    from .enums import LogLevel, ProcessingStatus

    # Create document lineage
    lineage = DocumentLineage(doc_id="doc123")

    # Add processing step
    add_processing_step(
        lineage,
        step_name="text_extraction",
        status=ProcessingStatus.SUCCESS,
        details={"chars": 5000}
    )

    # Log an error
    log_error_or_warning(
        lineage,
        log_level=LogLevel.ERROR,
        message="Failed to process images",
        metadata={"failed_pages": [1, 3]}
    )

    # Get recent errors
    since = datetime.now() - timedelta(hours=1)
    errors = get_error_logs(
        lineage,
        log_level=LogLevel.ERROR,
        start_time=since
    )
    ```
"""

from datetime import datetime, timezone
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .enums import LogLevel, ProcessingStatus
from .models import DocumentLineage, LogEntry, ProcessingStep

if TYPE_CHECKING:
    from .storage import LineageStorage

logger = logging.getLogger(__name__)


def add_processing_step(
    storage: Any,
    doc_id: str,
    step_name: str,
    status: Union[ProcessingStatus, str],
    details: Optional[Dict] = None,
    metrics: Optional[Dict] = None,
    error_message: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """
    Add a processing step to a document's lineage.

    This function records a processing operation performed on a document,
    including its status and any associated details.

    Args:
        storage: Storage interface to access document lineage
        doc_id: ID of the document to update
        step_name: Name of the processing step
        status: Status of the step (success/error/etc.)
        details: Optional step-specific details (e.g., metrics)
        metrics: Optional performance metrics for the step
        error_message: Optional error message if step failed
        timestamp: Optional timestamp for the step (defaults to current time)

    Example:
        ```python
        # Record successful text extraction
        add_processing_step(
            storage,
            doc_id="doc123",
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={
                "chars": 5000,
                "pages": 10,
                "language": "en"
            }
        )
        ```
    """
    lineage = storage.get_lineage(doc_id)
    if not lineage:
        raise ValueError(f"Document {doc_id} not found")

    if isinstance(status, str):
        status = ProcessingStatus(status.lower())

    step = ProcessingStep(
        step_name=step_name,
        status=status,
        details=details or {},
        metadata={
            "metrics": metrics or {},
            "error_message": error_message,
        },
        timestamp=timestamp or datetime.now(timezone.utc),
    )

    lineage.processing_steps.append(step)
    lineage.last_modified = datetime.now(timezone.utc)
    storage.save_lineage(lineage)


def get_processing_steps(
    storage_or_lineage: Union["LineageStorage", DocumentLineage],
    doc_id: Optional[str] = None,
    status: Optional[Union[ProcessingStatus, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[ProcessingStep]:
    """Get processing steps with optional filtering.

    Args:
        storage_or_lineage: Storage instance or DocumentLineage object
        doc_id: Optional document ID (required if storage is provided)
        status: Optional filter by processing status
        start_time: Optional filter for steps after this time
        end_time: Optional filter for steps before this time

    Returns:
        List of matching ProcessingStep objects
    """
    from .storage import LineageStorage  # Import here to avoid circular import

    if isinstance(storage_or_lineage, LineageStorage):
        if not doc_id:
            raise ValueError("doc_id is required when using storage")
        lineage = storage_or_lineage.get_lineage(doc_id)
        if not lineage:
            raise ValueError(f"Document {doc_id} not found")
    else:
        lineage = storage_or_lineage

    steps = lineage.processing_steps

    if status:
        if isinstance(status, str):
            status = ProcessingStatus(status.lower())
        steps = [step for step in steps if step.status == status]

    if start_time:
        steps = [step for step in steps if step.timestamp >= start_time]

    if end_time:
        steps = [step for step in steps if step.timestamp <= end_time]

    return steps


def log_error_or_warning(
    storage: Any,
    doc_id: str,
    level: Union[LogLevel, str],
    message: str,
    timestamp: Optional[datetime] = None,
    details: Optional[Dict] = None,
) -> None:
    """
    Log an error or warning for a document.

    Args:
        storage: Storage interface to access document lineage
        doc_id: ID of the document to update
        level: Log level (error/warning)
        message: Error/warning message
        timestamp: Optional timestamp for the log entry (defaults to current time)
        details: Optional additional details

    Example:
        ```python
        # Log an error
        log_error_or_warning(
            storage,
            doc_id="doc123",
            level=LogLevel.ERROR,
            message="Failed to process images",
            details={"failed_pages": [1, 3]}
        )
        ```
    """
    lineage = storage.get_lineage(doc_id)
    if not lineage:
        raise ValueError(f"Document {doc_id} not found")

    if isinstance(level, str):
        level = LogLevel(level.lower())

    log_entry = LogEntry(
        log_level=level,
        message=message,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata=details or {},
    )

    lineage.error_logs.append(log_entry)
    lineage.last_modified = datetime.now(timezone.utc)
    storage.save_lineage(lineage)


def get_error_logs(
    storage_or_lineage: Union["LineageStorage", DocumentLineage],
    doc_id: Optional[str] = None,
    log_level: Optional[Union[LogLevel, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[LogEntry]:
    """Get error logs with optional filtering.

    Args:
        storage_or_lineage: Storage instance or DocumentLineage object
        doc_id: Optional document ID (required if storage is provided)
        log_level: Optional filter by log level
        start_time: Optional filter for logs after this time
        end_time: Optional filter for logs before this time

    Returns:
        List of matching LogEntry objects
    """
    from .storage import LineageStorage  # Import here to avoid circular import

    if isinstance(storage_or_lineage, LineageStorage):
        if not doc_id:
            raise ValueError("doc_id is required when using storage")
        lineage = storage_or_lineage.get_lineage(doc_id)
        if not lineage:
            raise ValueError(f"Document {doc_id} not found")
    else:
        lineage = storage_or_lineage

    logs = lineage.error_logs

    if log_level:
        if isinstance(log_level, str):
            log_level = LogLevel(log_level.lower())
        logs = [log_entry for log_entry in logs if log_entry.log_level == log_level]

    if start_time:
        logs = [log_entry for log_entry in logs if log_entry.timestamp >= start_time]

    if end_time:
        logs = [log_entry for log_entry in logs if log_entry.timestamp <= end_time]

    return logs


def get_recent_errors(
    lineage_data: Dict[str, DocumentLineage],
    since: datetime,
) -> List[Dict[str, Any]]:
    """
    Get recent errors and warnings across all documents.

    This function aggregates recent error and warning logs from multiple documents,
    returning them in a format suitable for reporting or analysis.

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data
        since: Get errors since this timestamp

    Returns:
        List of dictionaries containing error information, sorted by timestamp
        (most recent first). Each dictionary includes:
            - doc_id: Document identifier
            - level: Log level (error/warning)
            - message: Error description
            - timestamp: When the error occurred
            - metadata: Additional context

    Example:
        ```python
        # Get errors from last hour
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(hours=1)
        recent = get_recent_errors(lineage_data, since)

        # Process results
        for error in recent:
            print(f"{error['timestamp']}: {error['level']} in {error['doc_id']}")
            print(f"Message: {error['message']}")
            if error['metadata']:
                print(f"Details: {error['metadata']}")
        ```
    """
    recent_errors = []
    for doc_id, lineage in lineage_data.items():
        error_logs = get_error_logs(lineage, start_time=since)
        for log in error_logs:
            recent_errors.append(
                {
                    "doc_id": doc_id,
                    "level": log.log_level.value,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat(),
                    "metadata": log.metadata,
                }
            )
    return sorted(recent_errors, key=lambda x: x["timestamp"], reverse=True)


def get_log_entries(log_list: List[Dict], start_time: Optional[datetime] = None) -> List[Dict]:
    """Get filtered log entries.

    Args:
        log_list: List of log entries
        start_time: Optional start time for filtering

    Returns:
        Filtered list of log entries
    """
    if not start_time:
        return log_list
    return [entry for entry in log_list if datetime.fromisoformat(entry["timestamp"]) >= start_time]
