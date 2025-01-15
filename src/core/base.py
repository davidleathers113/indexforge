"""Base service interface.

This module provides the base service class that defines the lifecycle and state
management interface that all services must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)


class AsyncContextManager(Protocol[T_co]):
    """Async context manager protocol."""

    @abstractmethod
    async def __aenter__(self) -> T_co:
        """Enter the async context."""
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Optional[bool]:
        """Exit the async context."""
        pass


class ServiceState(Enum):
    """Service lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceStateError(Exception):
    """Raised when a service operation fails due to invalid state.

    This can occur due to:
    - Service not initialized
    - Invalid state transition
    - Connection failures
    - Resource unavailability
    - Timeout conditions
    """

    pass


class ServiceMetrics(Protocol):
    """Protocol defining service metrics interface."""

    def get_uptime(self) -> timedelta:
        """Get service uptime."""
        pass

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage metrics."""
        pass


class BaseService(ABC, AsyncContextManager["BaseService"]):
    """Base class for all services.

    Provides:
    - Service lifecycle management (initialize/cleanup)
    - State management and transitions
    - Metadata and metrics tracking
    - Resource management
    - Health check interface
    - Context manager support
    """

    def __init__(self):
        """Initialize the base service."""
        self._state = ServiceState.CREATED
        self._metadata: Dict[str, str] = {}
        self._last_health_check: Optional[datetime] = None
        self._start_time: Optional[datetime] = None
        self._resource_usage: Dict[str, Any] = {}

    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        return self._state

    def _transition_state(self, new_state: ServiceState) -> None:
        """Transition service to new state.

        Args:
            new_state: Target state to transition to

        Raises:
            ServiceStateError: If transition is invalid
        """
        # Add state transition validation logic here if needed
        self._state = new_state

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service.

        This method should:
        - Establish connections
        - Allocate resources
        - Perform initial setup

        Raises:
            Exception: If initialization fails
        """
        self._transition_state(ServiceState.INITIALIZING)
        try:
            # Subclasses implement initialization logic
            self._start_time = datetime.now()
            self._transition_state(ServiceState.RUNNING)
        except Exception:
            self._transition_state(ServiceState.ERROR)
            raise

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources.

        This method should:
        - Close connections
        - Free resources
        - Reset state
        """
        self._transition_state(ServiceState.STOPPING)
        try:
            # Subclasses implement cleanup logic
            self._transition_state(ServiceState.STOPPED)
        except Exception:
            self._transition_state(ServiceState.ERROR)
            raise

    async def __aenter__(self) -> "BaseService":
        """Enter async context manager."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Optional[bool]:
        """Exit async context manager."""
        await self.cleanup()
        return None

    def _check_running(self) -> None:
        """Check if service is in running state.

        Raises:
            ServiceStateError: If service is not running
        """
        if self._state != ServiceState.RUNNING:
            raise ServiceStateError(f"Service not running (current state: {self._state.value})")

    def add_metadata(self, key: str, value: str) -> None:
        """Add metadata to the service.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value.

        Args:
            key: Metadata key

        Returns:
            Metadata value if found, None otherwise
        """
        return self._metadata.get(key)

    def get_uptime(self) -> Optional[timedelta]:
        """Get service uptime.

        Returns:
            Time since service initialization, or None if not started
        """
        if self._start_time:
            return datetime.now() - self._start_time
        return None

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage metrics.

        Returns:
            Dictionary of resource metrics
        """
        return self._resource_usage.copy()

    async def health_check(self) -> bool:
        """Check service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            self._check_running()
            self._last_health_check = datetime.now()
            return True
        except Exception:
            return False

    def get_last_health_check(self) -> Optional[datetime]:
        """Get timestamp of last health check.

        Returns:
            Datetime of last health check if performed, None otherwise
        """
        return self._last_health_check
