"""
Real-time status and monitoring functionality for document lineage tracking.

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
    from .models import DocumentLineage
    from .enums import ProcessingStatus

    # Create sample lineage data
    doc1 = DocumentLineage(doc_id="doc1")
    doc2 = DocumentLineage(doc_id="doc2")

    # Add processing steps
    doc1.processing_steps.append(ProcessingStep(
        step_name="extraction",
        status=ProcessingStatus.RUNNING
    ))
    doc2.processing_steps.append(ProcessingStep(
        step_name="indexing",
        status=ProcessingStatus.SUCCESS
    ))

    # Monitor active processes
    lineage_data = {"doc1": doc1, "doc2": doc2}
    active_count = count_active_processes(lineage_data)
    print(f"Active processes: {active_count}")

    # Get real-time status
    status = get_real_time_status(lineage_data)
    print(f"System status: {status['current_status']}")
    print(f"Active documents: {status['current_status']['active_documents']}")
    ```
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .enums import ProcessingStatus
from .metrics import get_aggregated_metrics
from .models import DocumentLineage, ProcessingStep

logger = logging.getLogger(__name__)


def get_latest_processing_step(lineage: DocumentLineage) -> Optional[ProcessingStep]:
    """
    Get the most recent processing step for a document.

    This function retrieves the latest processing step from a document's
    lineage, which represents the current state of document processing.

    Args:
        lineage: Document lineage data containing processing history

    Returns:
        Most recent ProcessingStep or None if no steps exist

    Example:
        ```python
        # Get latest step for a document
        latest_step = get_latest_processing_step(doc_lineage)
        if latest_step:
            print(f"Current status: {latest_step.status}")
            print(f"Step name: {latest_step.step_name}")
            print(f"Timestamp: {latest_step.timestamp}")
        ```
    """
    steps = lineage.processing_steps
    return steps[-1] if steps else None


def count_active_processes(lineage_data: Dict[str, DocumentLineage]) -> int:
    """
    Count the number of documents currently being processed.

    This function analyzes the processing status of all documents to
    determine how many are currently in an active processing state
    (not completed or failed).

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data

    Returns:
        Number of documents with active processing status

    Example:
        ```python
        # Monitor active processes
        active_count = count_active_processes(lineage_data)
        if active_count > 10:
            print(f"High system load: {active_count} active processes")
        else:
            print(f"Normal load: {active_count} active processes")
        ```
    """
    active_count = 0
    for lineage in lineage_data.values():
        latest_step = get_latest_processing_step(lineage)
        if latest_step and latest_step.status not in [
            ProcessingStatus.SUCCESS,
            ProcessingStatus.ERROR,
        ]:
            active_count += 1
    return active_count


def get_real_time_status(lineage_data: Dict[str, DocumentLineage]) -> Dict[str, Any]:
    """
    Get real-time system status and performance metrics.

    This function provides a comprehensive view of the current system state,
    including active processes, recent errors, processing rates, and
    performance metrics. It returns both current status and historical
    metrics for analysis.

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data

    Returns:
        Dictionary containing system status information:
            - current_status:
                - active_documents: Total number of documents
                - active_processes: Number of documents being processed
                - recent_metrics: Performance metrics for last hour
                - timestamp: Current timestamp
            - historical_metrics: Aggregated metrics across all time

    Example:
        ```python
        # Get system status
        status = get_real_time_status(lineage_data)

        # Check current state
        current = status['current_status']
        print(f"Active documents: {current['active_documents']}")
        print(f"Active processes: {current['active_processes']}")
        print(f"Recent success rate: {current['recent_metrics']['success_rate']:.2%}")

        # Analyze historical metrics
        history = status['historical_metrics']
        print(f"Overall success rate: {history['success_rate']:.2%}")
        print(f"Total processed: {history['total_processed']}")
        ```
    """
    now = datetime.now(timezone.utc)
    last_hour = now - timedelta(hours=1)

    return {
        "current_status": {
            "active_documents": len(lineage_data),
            "active_processes": count_active_processes(lineage_data),
            "recent_metrics": get_aggregated_metrics(lineage_data, start_time=last_hour),
            "timestamp": now.isoformat(),
        },
        "historical_metrics": get_aggregated_metrics(lineage_data),
    }
