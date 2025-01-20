"""Service state management.

This module provides state management functionality for ML services,
including state transitions, validation, and error handling.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Dict, Optional, Set

from .errors import ServiceStateError

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """States for ML service lifecycle."""

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    ERROR = auto()
    STOPPING = auto()
    STOPPED = auto()


class StateManager:
    """Manages service state transitions and validation.

    Provides:
    - State transition validation
    - State history tracking
    - Error handling for invalid transitions
    """

    # Valid state transitions
    _VALID_TRANSITIONS: Dict[ServiceState, Set[ServiceState]] = {
        ServiceState.UNINITIALIZED: {ServiceState.INITIALIZING},
        ServiceState.INITIALIZING: {ServiceState.RUNNING, ServiceState.ERROR},
        ServiceState.RUNNING: {ServiceState.STOPPING, ServiceState.ERROR},
        ServiceState.ERROR: {ServiceState.STOPPING, ServiceState.INITIALIZING},
        ServiceState.STOPPING: {ServiceState.STOPPED},
        ServiceState.STOPPED: {ServiceState.INITIALIZING},
    }

    def __init__(self) -> None:
        """Initialize the state manager."""
        self._current_state = ServiceState.UNINITIALIZED
        self._state_history: list[ServiceState] = [self._current_state]

    @property
    def current_state(self) -> ServiceState:
        """Get current state."""
        return self._current_state

    @property
    def state_history(self) -> list[ServiceState]:
        """Get state transition history."""
        return self._state_history.copy()

    def transition_to(self, new_state: ServiceState) -> None:
        """Transition to new state.

        Args:
            new_state: State to transition to

        Raises:
            ServiceStateError: If transition is invalid
        """
        if new_state not in self._VALID_TRANSITIONS[self._current_state]:
            raise ServiceStateError(
                f"Invalid state transition: {self._current_state} -> {new_state}"
            )

        logger.info(f"Service state transition: {self._current_state} -> {new_state}")
        self._current_state = new_state
        self._state_history.append(new_state)

    def validate_state(self, required_state: ServiceState) -> None:
        """Validate current state matches required state.

        Args:
            required_state: State that should be current

        Raises:
            ServiceStateError: If state is invalid
        """
        if self._current_state != required_state:
            raise ServiceStateError(
                f"Invalid service state: {self._current_state}, required: {required_state}"
            )

    def can_transition_to(self, target_state: ServiceState) -> bool:
        """Check if transition to target state is valid.

        Args:
            target_state: State to check transition to

        Returns:
            True if transition is valid
        """
        return target_state in self._VALID_TRANSITIONS[self._current_state]
