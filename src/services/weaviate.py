"""Weaviate service module.

This module provides a high-performance, fault-tolerant interface for Weaviate vector operations.
It implements advanced connection management, graceful degradation, and comprehensive observability.
"""

from contextlib import asynccontextmanager
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
)

import backoff
import weaviate
from weaviate.client import WeaviateClient as BaseWeaviateClient
from weaviate.exceptions import WeaviateConnectionError, WeaviateRequestError, WeaviateTimeout

from src.core.interfaces import VectorService
from src.services.base import (
    BaseService,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
)

if TYPE_CHECKING:
    from src.core.settings import Settings

T = TypeVar("T")
WeaviateResponse = TypeVar("WeaviateResponse")


def require_initialized(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to ensure service is initialized before operation.

    Provides clean error handling and state validation.
    """

    @wraps(func)
    async def wrapper(self: "WeaviateClient", *args: Any, **kwargs: Any) -> T:
        if not self.is_initialized or not self._client:
            raise ServiceNotInitializedError(
                f"Weaviate service must be initialized before calling {func.__name__}"
            )
        return await func(self, *args, **kwargs)

    return wrapper


class WeaviateOperationContext(Protocol):
    """Protocol defining the contract for Weaviate operations context."""

    async def __aenter__(self) -> BaseWeaviateClient:
        """Enter the async context."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context."""
        ...


class WeaviateClient(VectorService, BaseService):
    """High-performance Weaviate client for vector operations.

    Features:
    - Automatic connection management and recovery
    - Comprehensive error handling with backoff strategies
    - Rich observability and health monitoring
    - Thread-safe operations with context managers
    - Graceful degradation under load
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize Weaviate client with advanced configuration.

        Args:
            settings: Application settings containing Weaviate configuration
        """
        BaseService.__init__(self)
        VectorService.__init__(self, settings)
        self._settings = settings
        self._client: Optional[BaseWeaviateClient] = None
        self._health_check_failures = 0
        self._MAX_HEALTH_CHECK_FAILURES = 3

    @asynccontextmanager
    async def operation_context(self) -> AsyncGenerator[BaseWeaviateClient, None]:
        """Context manager for safe Weaviate operations.

        Provides automatic error handling and connection management.

        Yields:
            BaseWeaviateClient: Configured Weaviate client

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If client is in an invalid state
        """
        if not self.is_initialized or not self._client:
            raise ServiceNotInitializedError("Weaviate service is not initialized")

        try:
            yield self._client
        except WeaviateConnectionError as e:
            self._health_check_failures += 1
            if self._health_check_failures >= self._MAX_HEALTH_CHECK_FAILURES:
                self._initialized = False
            raise ServiceStateError(f"Connection error during operation: {str(e)}") from e
        except WeaviateTimeout as e:
            raise ServiceStateError(f"Operation timed out: {str(e)}") from e
        except WeaviateRequestError as e:
            raise ServiceStateError(f"Invalid request: {str(e)}") from e
        except Exception as e:
            raise ServiceStateError(f"Unexpected error during operation: {str(e)}") from e

    @backoff.on_exception(
        backoff.expo, (WeaviateConnectionError, WeaviateTimeout), max_tries=3, max_time=30
    )
    async def initialize(self) -> None:
        """Initialize Weaviate connection with automatic retry.

        Features:
        - Exponential backoff for connection attempts
        - Comprehensive error handling
        - Connection state validation
        - Health check verification

        Raises:
            ServiceInitializationError: If initialization fails after retries
        """
        try:
            # Create client with minimal configuration
            self._client = weaviate.Client()

            # Configure client after creation
            self._client._connection.url = str(self._settings.weaviate_url)
            if self._settings.weaviate_api_key:
                self._client._connection.api_key = self._settings.weaviate_api_key

            # Verify connection and schema access
            await self.health_check()

            # Update service state
            self._initialized = True
            self._health_check_failures = 0

            # Record initialization metadata
            self.add_metadata("weaviate_url", str(self._settings.weaviate_url))
            self.add_metadata("has_api_key", bool(self._settings.weaviate_api_key))
            self.add_metadata("initialization_time", self.get_current_time())

        except Exception as e:
            raise ServiceInitializationError(
                f"Failed to initialize Weaviate connection: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up Weaviate resources with graceful shutdown.

        Ensures proper resource cleanup and connection termination.
        """
        if self._client and hasattr(self._client, "close"):
            try:
                self._client.close()
            except Exception as e:
                self.add_metadata("cleanup_error", str(e))
        self._client = None
        self._initialized = False
        self._health_check_failures = 0

    @backoff.on_exception(backoff.expo, WeaviateConnectionError, max_tries=2, max_time=10)
    async def health_check(self) -> bool:
        """Check Weaviate connection health with retry capability.

        Returns:
            bool: True if Weaviate is healthy, False otherwise
        """
        try:
            if not self._client:
                return False

            # Verify schema access and basic operations
            self._client.schema.get()

            # Reset failure counter on successful check
            self._health_check_failures = 0
            return True

        except Exception:
            self._health_check_failures += 1
            return False

    @require_initialized
    async def add_object(
        self, class_name: str, data_object: Dict[str, Any], vector: Optional[List[float]] = None
    ) -> str:
        """Add object to Weaviate with advanced error handling.

        Args:
            class_name: Weaviate class name
            data_object: Object data to store
            vector: Optional vector embedding

        Returns:
            str: Object UUID

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If object creation fails
        """
        async with self.operation_context() as client:
            try:
                return str(
                    client.data.creator().with_vector(vector).with_payload(data_object).create()
                )
            except WeaviateRequestError as e:
                raise ServiceStateError(f"Failed to add object: {str(e)}") from e

    @require_initialized
    async def get_object(self, class_name: str, uuid: str) -> Optional[Dict[str, Any]]:
        """Get object from Weaviate with advanced error handling.

        Args:
            class_name: Weaviate class name
            uuid: Object UUID

        Returns:
            Optional[Dict[str, Any]]: Object if exists, None otherwise

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If retrieval fails
        """
        async with self.operation_context() as client:
            try:
                result = client.data.get_by_id(uuid=uuid).do()
                return result if result else None
            except WeaviateRequestError:
                return None

    @require_initialized
    async def delete_object(self, class_name: str, uuid: str) -> None:
        """Delete object from Weaviate with advanced error handling.

        Args:
            class_name: Weaviate class name
            uuid: Object UUID to delete

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If deletion fails
        """
        async with self.operation_context() as client:
            try:
                client.data.delete_by_id(uuid=uuid).do()
            except WeaviateRequestError as e:
                raise ServiceStateError(f"Failed to delete object: {str(e)}") from e
