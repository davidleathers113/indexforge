"""Vector service interfaces.

This module provides interfaces for vector database operations using the Command pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, TypeVar

if TYPE_CHECKING:
    from src.core.models.base import BaseModel
    from src.core.settings import Settings

T = TypeVar("T", bound="BaseModel")


@dataclass
class VectorCommand(Protocol[T]):
    """Base interface for vector operations."""

    def execute(self) -> T:
        """Execute the command.

        Returns:
            T: Command result

        Raises:
            ServiceStateError: If operation fails
        """
        ...


@dataclass
class AddObjectCommand(VectorCommand[str]):
    """Command for adding objects to vector store."""

    class_name: str
    data_object: Dict[str, Any]
    vector: Optional[List[float]] = None


@dataclass
class GetObjectCommand(VectorCommand[Optional[Dict[str, Any]]]):
    """Command for retrieving objects from vector store."""

    class_name: str
    uuid: str


@dataclass
class DeleteObjectCommand(VectorCommand[None]):
    """Command for deleting objects from vector store."""

    class_name: str
    uuid: str


@dataclass
class BatchAddCommand(VectorCommand[List[str]]):
    """Command for batch adding objects."""

    class_name: str
    objects: List[Dict[str, Any]]
    vectors: Optional[List[List[float]]] = None
    batch_size: Optional[int] = None


@dataclass
class BatchDeleteCommand(VectorCommand[None]):
    """Command for batch deleting objects."""

    class_name: str
    uuids: List[str]
    batch_size: Optional[int] = None


@dataclass
class VectorSearchCommand(VectorCommand[List[Dict[str, Any]]]):
    """Command for vector similarity search."""

    class_name: str
    vector: List[float]
    limit: int = 10
    distance_threshold: float = 0.8
    with_payload: bool = True


class VectorService(ABC):
    """Interface for vector database services."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the vector service.

        Args:
            settings: Application settings
        """
        self._settings = settings
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service.

        Raises:
            ServiceInitializationError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources."""
        ...

    @abstractmethod
    async def execute(self, command: VectorCommand[T]) -> T:
        """Execute a vector operation command.

        Args:
            command: Operation command to execute

        Returns:
            T: Command result

        Raises:
            ServiceStateError: If operation fails
            ValueError: If command is invalid
        """
        ...
