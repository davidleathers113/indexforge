"""Base ML service implementation.

This module provides the base ML service class that integrates with the service
architecture while providing ML-specific functionality and state management.
"""

from abc import abstractmethod
from typing import Generic, TypeVar

from src.core.errors import ServiceInitializationError
from src.services.base import BaseService

T = TypeVar("T")  # Type of ML model
P = TypeVar("P")  # Type of model parameters


class MLService(BaseService, Generic[T, P]):
    """Base class for ML services.

    Provides:
    - Integration with service architecture
    - ML model lifecycle management
    - State tracking and validation
    - Resource cleanup
    """

    def __init__(self) -> None:
        """Initialize the ML service."""
        super().__init__()
        self._model: T | None = None
        self._parameters: P | None = None

    @property
    def model(self) -> T | None:
        """Get the current ML model instance."""
        return self._model

    @property
    def parameters(self) -> P | None:
        """Get the current model parameters."""
        return self._parameters

    @abstractmethod
    async def load_model(self, parameters: P) -> T:
        """Load ML model with given parameters.

        Args:
            parameters: Model parameters

        Returns:
            Loaded model instance

        Raises:
            ServiceInitializationError: If model loading fails
        """
        ...

    async def initialize(self) -> None:
        """Initialize the ML service.

        This implementation:
        1. Loads model parameters
        2. Initializes the model
        3. Verifies model is ready
        4. Sets initialized state

        Raises:
            ServiceInitializationError: If initialization fails
        """
        try:
            self._parameters = await self._load_parameters()
            self._model = await self.load_model(self._parameters)
            self._initialized = True
            self.add_metadata("initialized_at", self.get_current_time())
        except Exception as e:
            raise ServiceInitializationError(f"Failed to initialize ML service: {e}") from e

    async def cleanup(self) -> None:
        """Clean up ML service resources.

        This implementation:
        1. Releases model resources
        2. Clears parameters
        3. Resets initialization state
        """
        self._model = None
        self._parameters = None
        self._initialized = False
        self.add_metadata("cleaned_up_at", self.get_current_time())

    async def health_check(self) -> bool:
        """Check ML service health status.

        Returns:
            True if service is initialized and model is loaded
        """
        return self.is_initialized and self._model is not None

    @abstractmethod
    async def _load_parameters(self) -> P:
        """Load model parameters.

        Returns:
            Model parameters

        Raises:
            ServiceInitializationError: If parameter loading fails
        """
        ...
