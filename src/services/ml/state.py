"""ML service state management.

This module provides state management functionality for ML services,
including state tracking, validation, and transition management.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Dict, Set

from src.core.errors import ServiceStateError

logger = logging.getLogger(__name__)


class MLServiceState(Enum):
    """States for ML service lifecycle."""

    UNINITIALIZED = auto()
    LOADING = auto()
    READY = auto()
    PROCESSING = auto()
    ERROR = auto()
    STOPPING = auto()
    STOPPED = auto()


class StateManager:
    """Manages ML service state transitions and validation.

    Provides:
    - State transition validation
    - State history tracking
    - Error handling for invalid transitions
    """

    # Valid state transitions
    _VALID_TRANSITIONS: Dict[MLServiceState, Set[MLServiceState]] = {
        MLServiceState.UNINITIALIZED: {MLServiceState.LOADING},
        MLServiceState.LOADING: {MLServiceState.READY, MLServiceState.ERROR},
        MLServiceState.READY: {
            MLServiceState.PROCESSING,
            MLServiceState.STOPPING,
            MLServiceState.ERROR,
        },
        MLServiceState.PROCESSING: {MLServiceState.READY, MLServiceState.ERROR},
        MLServiceState.ERROR: {MLServiceState.STOPPING, MLServiceState.LOADING},
        MLServiceState.STOPPING: {MLServiceState.STOPPED},
        MLServiceState.STOPPED: {MLServiceState.LOADING},
    }

    def __init__(self) -> None:
        """Initialize the state manager."""
        self._current_state = MLServiceState.UNINITIALIZED
        self._state_history: list[MLServiceState] = [self._current_state]

    @property
    def current_state(self) -> MLServiceState:
        """Get current state."""
        return self._current_state

    @property
    def state_history(self) -> list[MLServiceState]:
        """Get state transition history."""
        return self._state_history.copy()

    def transition_to(self, new_state: MLServiceState) -> None:
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

        logger.info(f"ML service state transition: {self._current_state} -> {new_state}")
        self._current_state = new_state
        self._state_history.append(new_state)

    def validate_state(self, required_state: MLServiceState) -> None:
        """Validate current state matches required state.

        Args:
            required_state: State that should be current

        Raises:
            ServiceStateError: If state is invalid
        """
        if self._current_state != required_state:
            raise ServiceStateError(
                f"Invalid ML service state: {self._current_state}, required: {required_state}"
            )

    def can_transition_to(self, target_state: MLServiceState) -> bool:
        """Check if transition to target state is valid.

        Args:
            target_state: State to check transition to

        Returns:
            True if transition is valid
        """
        return target_state in self._VALID_TRANSITIONS[self._current_state]
