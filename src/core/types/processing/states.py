"""Processing states and status enums.

This module defines the states and status enums used in processing operations,
providing a consistent way to track and manage processing state.

Key Features:
    - Processing status tracking
    - State transitions
    - Status validation
"""

from enum import Enum, auto


class ProcessingStatus(Enum):
    """Status of document processing."""

    PENDING = auto()  # Document is queued for processing
    PROCESSING = auto()  # Document is currently being processed
    COMPLETED = auto()  # Document processing completed successfully
    FAILED = auto()  # Document processing failed
    CANCELLED = auto()  # Document processing was cancelled
    RETRYING = auto()  # Document processing is being retried
    SKIPPED = auto()  # Document processing was skipped
    UNKNOWN = auto()  # Document processing status is unknown

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal status.

        Returns:
            bool: True if status is terminal (completed, failed, cancelled, skipped)
        """
        return self in {
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            ProcessingStatus.CANCELLED,
            ProcessingStatus.SKIPPED,
        }

    @property
    def is_active(self) -> bool:
        """Check if this is an active status.

        Returns:
            bool: True if status is active (processing, retrying)
        """
        return self in {ProcessingStatus.PROCESSING, ProcessingStatus.RETRYING}

    @property
    def is_pending(self) -> bool:
        """Check if this is a pending status.

        Returns:
            bool: True if status is pending
        """
        return self == ProcessingStatus.PENDING

    @property
    def is_error(self) -> bool:
        """Check if this is an error status.

        Returns:
            bool: True if status indicates an error (failed)
        """
        return self == ProcessingStatus.FAILED
