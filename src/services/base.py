"""Base service definitions for external integrations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class ServiceError(Exception):
    """Base exception for service-related errors."""

    pass


class ServiceNotInitializedError(ServiceError):
    """Raised when attempting to use a service that hasn't been initialized."""

    pass


class ServiceInitializationError(ServiceError):
    """Raised when a service fails to initialize."""

    pass


class ServiceStateError(ServiceError):
    """Raised when a service operation fails due to invalid state.

    This exception indicates that a service operation could not be completed
    due to the current state of the service. This could be due to:
    - Connection failures
    - Resource unavailability
    - Invalid operation sequences
    - Timeout conditions
    - Resource exhaustion
    """

    pass


class BaseService(ABC):
    """Base contract for all services.

    All external service integrations must inherit from this base class
    to ensure consistent initialization, cleanup, and health monitoring.
    """

    def __init__(self) -> None:
        self._initialized: bool = False
        self._metadata: Dict[str, Any] = {}

    @property
    def is_initialized(self) -> bool:
        """Check if the service has been initialized."""
        return self._initialized

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get service metadata."""
        return self._metadata.copy()

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service connections and resources.

        This method should:
        1. Set up any necessary connections
        2. Verify the connection is working
        3. Initialize any required resources
        4. Set self._initialized to True on success

        Raises:
            ServiceInitializationError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources and connections.

        This method should:
        1. Close any open connections
        2. Release any held resources
        3. Set self._initialized to False
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health status.

        Returns:
            bool: True if the service is healthy, False otherwise
        """
        ...

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the service.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Optional[Any]: Metadata value if exists, None otherwise
        """
        return self._metadata.get(key)

    def get_current_time(self) -> str:
        """Get current time in ISO format.

        Returns:
            str: Current time in ISO format
        """
        return datetime.utcnow().isoformat()
