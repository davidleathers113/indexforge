"""Error logging lifecycle management.

This module provides the ErrorLoggingManager class for handling the complete
lifecycle of error logs, including creation, storage, and retrieval.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Union

from src.core.monitoring.errors.models.log_entry import LogEntry, LogLevel

logger = logging.getLogger(__name__)


class ErrorLoggingManager:
    """Manages the lifecycle of error and warning logs.

    This class handles log entry creation, storage, and retrieval while ensuring
    proper validation and persistence of log data.

    Example:
        ```python
        manager = ErrorLoggingManager(storage_instance)

        # Log an error
        manager.log_error_or_warning(
            doc_id="doc123",
            message="Failed to process document",
            level=LogLevel.ERROR,
            metadata={"error_code": "PROC_001"}
        )

        # Retrieve logs
        logs = manager.get_error_logs(
            doc_id="doc123",
            log_level=LogLevel.ERROR,
            start_time=datetime(2024, 1, 1, tzinfo=UTC)
        )
        ```

    Attributes:
        storage: Storage backend for persisting log entries
    """

    def __init__(self, storage: Any) -> None:
        """Initialize the error logging manager.

        Args:
            storage: Storage backend instance for persisting logs
        """
        self.storage = storage

    def log_error_or_warning(
        self,
        doc_id: str,
        message: str,
        level: Union[LogLevel, str],
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error or warning message for a document.

        Args:
            doc_id: ID of the document to log for
            message: Error or warning message
            level: Level of the log (ERROR or WARNING)
            timestamp: Optional timestamp (defaults to current time)
            metadata: Optional metadata about the error/warning

        Raises:
            ValueError: If document not found or invalid log level
            RuntimeError: If storage operation fails

        Example:
            ```python
            manager.log_error_or_warning(
                doc_id="doc123",
                message="Invalid document format",
                level=LogLevel.WARNING,
                metadata={"format": "PDF", "version": "1.4"}
            )
            ```
        """
        logger.debug(
            "Logging message for document %s - Level: %s, Message: %s",
            doc_id,
            level,
            message,
        )
        logger.debug("Metadata: %s", metadata)

        # Validate input parameters
        if not doc_id or not message:
            logger.error("Invalid parameters - Doc ID: %s, Message: %s", doc_id, message)
            raise ValueError("Document ID and message must be provided")

        try:
            # Convert string log level to enum if needed
            if isinstance(level, str):
                try:
                    level = LogLevel[level.upper()]
                except KeyError:
                    logger.error("Invalid log level: %s", level)
                    raise ValueError(f"Invalid log level: {level}")

            # Get document lineage
            lineage = self.storage.get_lineage(doc_id)
            if not lineage:
                logger.error("Document %s not found", doc_id)
                raise ValueError(f"Document {doc_id} not found")

            # Create log entry
            log_entry = LogEntry(
                message=message,
                log_level=level,
                timestamp=timestamp or datetime.now(UTC),
                metadata=metadata,
            )

            # Add to error logs
            lineage.error_logs.append(log_entry)
            lineage.last_modified = datetime.now(UTC)

            # Save updated lineage
            self.storage.save_lineage(lineage)
            logger.debug("Successfully added log entry to document %s", doc_id)

        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to log error/warning: %s", str(e))
            raise RuntimeError(f"Failed to log error/warning: {str(e)}") from e

    def get_error_logs(
        self,
        doc_id: str,
        log_level: Optional[Union[LogLevel, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[LogEntry]:
        """Get error/warning logs for a document, optionally filtered.

        Args:
            doc_id: ID of the document to get logs for
            log_level: Optional level to filter by (ERROR or WARNING)
            start_time: Optional start of time range to filter by
            end_time: Optional end of time range to filter by

        Returns:
            List of matching log entries

        Raises:
            ValueError: If document not found or invalid log level
            RuntimeError: If storage operation fails

        Example:
            ```python
            # Get all ERROR logs from the last hour
            logs = manager.get_error_logs(
                doc_id="doc123",
                log_level=LogLevel.ERROR,
                start_time=datetime.now(UTC) - timedelta(hours=1)
            )
            ```
        """
        logger.debug(
            "Getting logs for document %s - Level: %s, Time range: %s to %s",
            doc_id,
            log_level,
            start_time,
            end_time,
        )

        try:
            # Convert string log level to enum if needed
            if isinstance(log_level, str):
                try:
                    log_level = LogLevel[log_level.upper()]
                except KeyError:
                    logger.error("Invalid log level: %s", log_level)
                    raise ValueError(f"Invalid log level: {log_level}")

            # Get document lineage
            lineage = self.storage.get_lineage(doc_id)
            if not lineage:
                logger.error("Document %s not found", doc_id)
                raise ValueError(f"Document {doc_id} not found")

            # Convert stored logs to LogEntry objects
            logs = [
                LogEntry.from_dict(log) if isinstance(log, dict) else log
                for log in lineage.error_logs
            ]

            # Apply filters
            if log_level:
                logs = [log for log in logs if log.log_level == log_level]
            if start_time:
                logs = [log for log in logs if log.timestamp >= start_time]
            if end_time:
                logs = [log for log in logs if log.timestamp <= end_time]

            logger.debug("Found %d matching log entries", len(logs))
            return logs

        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to get error logs: %s", str(e))
            raise RuntimeError(f"Failed to get error logs: {str(e)}") from e
