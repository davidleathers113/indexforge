"""Base service functionality for ML components.

This module provides the foundational service classes and protocols for ML services,
including state management, initialization, and cleanup.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, TypeVar

from .errors import ServiceInitializationError, ServiceNotInitializedError
from .state import ServiceState, StateManager

T = TypeVar("T")
P = TypeVar("P")

logger = logging.getLogger(__name__)


class ServiceProtocol(Protocol):
    """Protocol defining the core service interface."""

    @property
    def state(self) -> ServiceState:
        """Get the current service state."""
        ...

    async def initialize(self) -> None:
        """Initialize the service."""
        ...

    async def cleanup(self) -> None:
        """Clean up service resources."""
        ...

    def validate_state(self, required_state: ServiceState) -> None:
        """Validate service is in required state."""
        ...


class BaseService(ABC):
    """Base class for ML services.

    Provides core functionality for:
    - State management
    - Initialization/cleanup
    - Resource tracking
    - Error handling
    """

    def __init__(self) -> None:
        """Initialize the base service."""
        self._state_manager = StateManager()
        self._metadata: dict[str, Any] = {}

    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        return self._state_manager.current_state

    @property
    def metadata(self) -> dict[str, Any]:
        """Get service metadata."""
        return self._metadata.copy()

    def validate_state(self, required_state: ServiceState) -> None:
        """Validate service is in required state.

        Args:
            required_state: State the service should be in

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If service is in invalid state
        """
        self._state_manager.validate_state(required_state)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service.

        Raises:
            ServiceInitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources."""
        pass

    def update_metadata(self, key: str, value: Any) -> None:
        """Update service metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value
