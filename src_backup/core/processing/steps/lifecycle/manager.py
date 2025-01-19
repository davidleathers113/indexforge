"""Processing step lifecycle management.

This module provides the ProcessingStepManager class for tracking and managing
document processing operations throughout their lifecycle.
"""

from datetime import UTC, datetime
import logging
from typing import Any

from src.core.processing.steps.models.step import ProcessingStatus, ProcessingStep


logger = logging.getLogger(__name__)


class ProcessingStepManager:
    """Manages document processing step lifecycle.

    This class handles the creation, tracking, and querying of processing steps
    for documents, including performance metrics and error tracking.

    Example:
        ```python
        manager = ProcessingStepManager(storage_instance)

        # Record a processing step
        manager.add_step(
            doc_id="doc123",
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"chars": 5000, "pages": 10},
            metrics={"duration_ms": 1500}
        )

        # Get steps for analysis
        steps = manager.get_steps(
            doc_id="doc123",
            status=ProcessingStatus.ERROR,
            start_time=datetime.now(UTC) - timedelta(hours=1)
        )
        ```

    Attributes:
        storage: Storage backend for persisting processing steps
    """

    def __init__(self, storage: Any) -> None:
        """Initialize the processing step manager.

        Args:
            storage: Storage backend instance for persisting steps
        """
        self.storage = storage

    def add_step(
        self,
        doc_id: str,
        step_name: str,
        status: ProcessingStatus | str,
        details: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        error_message: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Add a processing step to a document's history.

        Args:
            doc_id: ID of the document being processed
            step_name: Name of the processing step
            status: Status of the step
            details: Optional step-specific details
            metrics: Optional performance metrics
            error_message: Optional error message if step failed
            timestamp: Optional timestamp (defaults to current UTC time)

        Raises:
            ValueError: If document not found or invalid status
            RuntimeError: If storage operation fails

        Example:
            ```python
            manager.add_step(
                doc_id="doc123",
                step_name="image_processing",
                status=ProcessingStatus.WARNING,
                details={"processed": 8, "skipped": 2},
                metrics={"duration_ms": 2500},
                error_message="2 images failed quality check"
            )
            ```
        """
        logger.debug(
            "Adding processing step for document %s - Step: %s, Status: %s",
            doc_id,
            step_name,
            status,
        )

        try:
            # Get document lineage
            lineage = self.storage.get_lineage(doc_id)
            if not lineage:
                raise ValueError(f"Document {doc_id} not found")

            # Convert string status to enum if needed
            if isinstance(status, str):
                try:
                    status = ProcessingStatus(status.lower())
                except ValueError:
                    logger.error("Invalid processing status: %s", status)
                    raise ValueError(f"Invalid processing status: {status}")

            # Create and add step
            step = ProcessingStep(
                step_name=step_name,
                status=status,
                details=details or {},
                metadata={
                    "metrics": metrics or {},
                    "error_message": error_message,
                },
                timestamp=timestamp or datetime.now(UTC),
            )

            lineage.processing_steps.append(step)
            lineage.last_modified = datetime.now(UTC)
            self.storage.save_lineage(lineage)

            logger.debug(
                "Successfully added step %s for document %s with status %s",
                step_name,
                doc_id,
                status.value,
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to add processing step: %s", str(e))
            raise RuntimeError(f"Failed to add processing step: {e!s}") from e

    def get_steps(
        self,
        doc_id: str,
        status: ProcessingStatus | str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[ProcessingStep]:
        """Get processing steps with optional filtering.

        Args:
            doc_id: ID of the document to get steps for
            status: Optional filter by processing status
            start_time: Optional filter for steps after this time
            end_time: Optional filter for steps before this time

        Returns:
            List of matching ProcessingStep objects

        Raises:
            ValueError: If document not found or invalid status
            RuntimeError: If storage operation fails

        Example:
            ```python
            # Get all failed steps from the last hour
            steps = manager.get_steps(
                doc_id="doc123",
                status=ProcessingStatus.FAILED,
                start_time=datetime.now(UTC) - timedelta(hours=1)
            )
            ```
        """
        logger.debug(
            "Getting steps for document %s - Status: %s, Time range: %s to %s",
            doc_id,
            status,
            start_time,
            end_time,
        )

        try:
            # Get document lineage
            lineage = self.storage.get_lineage(doc_id)
            if not lineage:
                raise ValueError(f"Document {doc_id} not found")

            # Convert string status to enum if needed
            if isinstance(status, str):
                try:
                    status = ProcessingStatus(status.lower())
                except ValueError:
                    logger.error("Invalid processing status: %s", status)
                    raise ValueError(f"Invalid processing status: {status}")

            # Get steps and apply filters
            steps = lineage.processing_steps

            if status:
                steps = [step for step in steps if step.status == status]
            if start_time:
                steps = [step for step in steps if step.timestamp >= start_time]
            if end_time:
                steps = [step for step in steps if step.timestamp <= end_time]

            logger.debug("Found %d matching steps", len(steps))
            return steps

        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to get processing steps: %s", str(e))
            raise RuntimeError(f"Failed to get processing steps: {e!s}") from e

    def get_recent_errors(
        self,
        since: datetime,
        include_warnings: bool = False,
    ) -> list[dict[str, Any]]:
        """Get recent processing errors across all documents.

        Args:
            since: Get errors after this time
            include_warnings: Whether to include warning status steps

        Returns:
            List of error details with document IDs

        Example:
            ```python
            # Get errors from the last hour
            errors = manager.get_recent_errors(
                since=datetime.now(UTC) - timedelta(hours=1)
            )
            for error in errors:
                print(f"Document {error['doc_id']}: {error['error_message']}")
            ```
        """
        logger.debug("Getting recent errors since %s", since)

        try:
            error_states = {ProcessingStatus.ERROR, ProcessingStatus.FAILED}
            if include_warnings:
                error_states.add(ProcessingStatus.WARNING)

            errors = []
            lineage_data = self.storage.get_all_lineage()

            for doc_id, lineage in lineage_data.items():
                for step in lineage.processing_steps:
                    if (
                        step.status in error_states
                        and step.timestamp >= since
                        and step.error_message
                    ):
                        errors.append(
                            {
                                "doc_id": doc_id,
                                "step_name": step.step_name,
                                "status": step.status.value,
                                "error_message": step.error_message,
                                "timestamp": step.timestamp,
                                "details": step.details,
                            }
                        )

            logger.debug("Found %d recent errors", len(errors))
            return sorted(errors, key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            logger.error("Failed to get recent errors: %s", str(e))
            raise RuntimeError(f"Failed to get recent errors: {e!s}") from e
