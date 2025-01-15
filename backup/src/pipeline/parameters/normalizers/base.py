"""Base normalizer implementation."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Normalizer(Generic[T, U], ABC):
    """Base class for all normalizers."""

    @abstractmethod
    def normalize(self, value: T) -> U:
        """Normalize a value.

        Args:
            value: Value to normalize

        Returns:
            Normalized value
        """
        pass
