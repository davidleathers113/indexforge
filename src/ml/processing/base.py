"""Base processor implementation with core functionality."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from src.core.models.documents import DocumentStatus, ProcessingStep
from src.core.types.processing import ProcessingStateError
from src.core.types.service import ServiceState
from src.services.base import BaseService

from .models import ProcessingStrategy, ServiceNotInitializedError

if TYPE_CHECKING:
    from src.core.settings import Settings

T = TypeVar("T")
StrategyResult = TypeVar("StrategyResult")


class BaseProcessor(BaseService, Generic[StrategyResult], ABC):
    """Base class for all processors.

    Provides core functionality for processor lifecycle management,
    strategy registration, and error handling.

    Type Parameters:
        StrategyResult: The type of result produced by this processor's strategies

    Attributes:
        settings: Application settings
        state: Current service state
        strategies: Registered processing strategies
        metadata: Processing metadata
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize the processor.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        super().__init__()
        self.settings = settings
        self._strategies: list[ProcessingStrategy[StrategyResult]] = []
        self._state = ServiceState.CREATED
        self._metadata: dict[str, Any] = {}

    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        return self._state

    @property
    def is_initialized(self) -> bool:
        """Check if processor is initialized."""
        return self._state == ServiceState.RUNNING

    def add_strategy(self, strategy: ProcessingStrategy[StrategyResult]) -> None:
        """Add a processing strategy.

        Args:
            strategy: Strategy to add

        Raises:
            ValueError: If strategy is None
            ProcessingStateError: If processor is not in CREATED state
        """
        if strategy is None:
            raise ValueError("Strategy cannot be None")

        if self._state != ServiceState.CREATED:
            raise ProcessingStateError(
                message=f"Cannot add strategy in {self._state} state",
                current_state=self._state,
                expected_states={ServiceState.CREATED},
                service_name=self.__class__.__name__,
            )

        self._strategies.append(strategy)

    def _transition_state(self, new_state: ServiceState) -> None:
        """Transition to a new state.

        Args:
            new_state: State to transition to

        Raises:
            ProcessingStateError: If transition is invalid
        """
        valid_transitions = {
            ServiceState.CREATED: {ServiceState.INITIALIZING, ServiceState.ERROR},
            ServiceState.INITIALIZING: {ServiceState.RUNNING, ServiceState.ERROR},
            ServiceState.RUNNING: {ServiceState.STOPPING, ServiceState.ERROR},
            ServiceState.STOPPING: {ServiceState.STOPPED, ServiceState.ERROR},
            ServiceState.STOPPED: {ServiceState.INITIALIZING},
            ServiceState.ERROR: {ServiceState.INITIALIZING},
        }

        if new_state not in valid_transitions.get(self._state, set()):
            raise ProcessingStateError(
                message=f"Invalid state transition from {self._state} to {new_state}",
                current_state=self._state,
                expected_states=valid_transitions[self._state],
                service_name=self.__class__.__name__,
            )

        self._state = new_state

    def _check_running(self) -> None:
        """Check if the processor is in running state.

        Raises:
            ServiceNotInitializedError: If processor is not initialized
            ProcessingStateError: If processor is in an invalid state
        """
        if self._state != ServiceState.RUNNING:
            if self._state == ServiceState.CREATED:
                raise ServiceNotInitializedError(
                    "Processor not initialized",
                    service_name=self.__class__.__name__,
                    current_state=self._state.value,
                    required_state=ServiceState.RUNNING.value,
                )
            raise ProcessingStateError(
                message=f"Processor in invalid state: {self._state.value}. Required state: {ServiceState.RUNNING.value}",
                current_state=self._state,
                expected_states={ServiceState.RUNNING},
                service_name=self.__class__.__name__,
            )

    @abstractmethod
    def _initialize_strategies(self) -> None:
        """Initialize all registered strategies.

        This method should be called during processor initialization
        to set up any resources needed by the strategies.

        Raises:
            ServiceInitializationError: If strategy initialization fails
        """
        pass

    def cleanup(self) -> None:
        """Clean up resources.

        This method ensures proper cleanup of all resources,
        including those held by strategies.
        """
        self._strategies.clear()
        self._metadata.clear()
        self._transition_state(ServiceState.STOPPED)

    def get_processing_steps(self) -> list[ProcessingStep]:
        """Get processing steps applied by this processor.

        Returns:
            List of processing steps with their current status
        """
        return [
            ProcessingStep(
                step_name=str(i),
                status=DocumentStatus.PROCESSED,
                error_message=None,
                completed_at=None,
            )
            for i, _ in enumerate(self._strategies)
        ]

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata for the current processing operation.

        Args:
            key: Metadata key
            value: Metadata value

        Raises:
            ValueError: If key is invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("Metadata key must be a non-empty string")
        self._metadata[key] = value

    def get_metadata(self) -> dict[str, Any]:
        """Get current processing metadata.

        Returns:
            Dictionary of metadata key-value pairs
        """
        return self._metadata.copy()

    def clear_metadata(self) -> None:
        """Clear all processing metadata."""
        self._metadata.clear()
