"""
Handles error and warning logging for document processing.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Union

from .enums import LogLevel

logger = logging.getLogger(__name__)


class LogEntry:
    """Represents a log entry in the error/warning log."""

    def __init__(
        self,
        message: str,
        log_level: LogLevel,
        timestamp: datetime,
        metadata: Optional[Dict] = None,
    ):
        self.message = message
        self.log_level = log_level
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        """Convert the log entry to a dictionary for storage."""
        return {
            "message": self.message,
            "level": self.log_level.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "LogEntry":
        """Create a LogEntry instance from a dictionary."""
        return cls(
            message=data["message"],
            log_level=LogLevel(data["level"]),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


def log_error_or_warning(
    storage,
    doc_id: str,
    message: str,
    level: Union[LogLevel, str],
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Log an error or warning message for a document.

    Args:
        storage: LineageStorage instance
        doc_id: ID of the document to log for
        message: Error or warning message
        level: Level of the log (ERROR or WARNING)
        timestamp: Optional timestamp for the log entry (defaults to current time)
        metadata: Optional metadata about the error/warning

    Raises:
        ValueError: If document not found or invalid log level
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
        lineage = storage.get_lineage(doc_id)
        if not lineage:
            logger.error("Document %s not found", doc_id)
            raise ValueError(f"Document {doc_id} not found")

        # Create log entry with provided or current timestamp
        log_entry = LogEntry(
            message=message,
            log_level=level,
            timestamp=timestamp or datetime.now(timezone.utc),
            metadata=metadata,
        )

        # Add to error logs
        lineage.error_logs.append(log_entry)
        lineage.last_modified = datetime.now(timezone.utc)

        # Save updated lineage
        storage.save_lineage(lineage)
        logger.debug("Successfully added log entry to document %s", doc_id)

    except Exception as e:
        logger.error("Failed to log error/warning: %s", str(e))
        raise


def get_error_logs(
    storage,
    doc_id: str,
    log_level: Optional[Union[LogLevel, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[LogEntry]:
    """Get error/warning logs for a document, optionally filtered by level and time range.

    Args:
        storage: LineageStorage instance
        doc_id: ID of the document to get logs for
        log_level: Optional level to filter by (ERROR or WARNING)
        start_time: Optional start of time range to filter by
        end_time: Optional end of time range to filter by

    Returns:
        List of matching log entries

    Raises:
        ValueError: If document not found or invalid log level
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
        lineage = storage.get_lineage(doc_id)
        if not lineage:
            logger.error("Document %s not found", doc_id)
            raise ValueError(f"Document {doc_id} not found")

        # Convert stored logs to LogEntry objects
        logs = [
            LogEntry.from_dict(log) if isinstance(log, dict) else log for log in lineage.error_logs
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

    except Exception as e:
        logger.error("Failed to get error logs: %s", str(e))
        raise
