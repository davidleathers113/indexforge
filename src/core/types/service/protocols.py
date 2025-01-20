"""Service protocol definitions.

This module defines core protocols for service implementations,
including async context management and service lifecycle protocols.
"""

from abc import abstractmethod
from typing import Any, Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)


class AsyncContextManager(Protocol[T_co]):
    """Async context manager protocol.

    This protocol defines the interface for types that can be used
    as async context managers.
    """

    @abstractmethod
    async def __aenter__(self) -> T_co:
        """Enter the async context.

        Returns:
            The context manager instance
        """
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> bool | None:
        """Exit the async context.

        Args:
            exc_type: The type of the exception that was raised
            exc_val: The instance of the exception that was raised
            exc_tb: The traceback of the exception

        Returns:
            True if the exception was handled, None otherwise
        """
        pass
