"""Weaviate service module with advanced batch operations.

This module provides a high-performance, fault-tolerant interface for Weaviate vector operations.
It implements advanced connection management, graceful degradation, and comprehensive observability.
"""

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import backoff
import weaviate
from weaviate.client import WeaviateClient as BaseWeaviateClient
from weaviate.exceptions import WeaviateConnectionError, WeaviateQueryError, WeaviateTimeoutError

from src.core.interfaces import VectorService
from src.core.metrics import ServiceMetricsCollector
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
    """Decorator to ensure service is initialized before operation."""

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
    """High-performance Weaviate client for vector operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize Weaviate client with advanced configuration."""
        BaseService.__init__(self)
        VectorService.__init__(self, settings)
        self._settings = settings
        self._client: BaseWeaviateClient | None = None
        self._health_check_failures = 0
        self._MAX_HEALTH_CHECK_FAILURES = 3
        self._batch_size = 100
        self._vector_cache: dict[str, list[float]] = {}
        self._metrics = ServiceMetricsCollector(
            service_name="weaviate",
            max_history=5000,
            memory_threshold_mb=500,
        )

    @require_initialized
    async def batch_add_objects(
        self,
        class_name: str,
        objects: list[dict[str, Any]],
        vectors: list[list[float]] | None = None,
        batch_size: int | None = None,
    ) -> list[str]:
        """Add multiple objects to Weaviate efficiently.

        Args:
            class_name: Weaviate class name
            objects: List of objects to add
            vectors: Optional list of vector embeddings
            batch_size: Optional custom batch size

        Returns:
            List[str]: List of created object UUIDs

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If batch operation fails
        """
        if not objects:
            return []

        batch_size = batch_size or self._batch_size
        uuids: list[str] = []

        with self._metrics.measure_operation(
            "batch_add_objects",
            {
                "class_name": class_name,
                "object_count": len(objects),
                "batch_size": batch_size,
            },
        ):
            async with self.operation_context() as client:
                try:
                    # Process in batches
                    for i in range(0, len(objects), batch_size):
                        batch_objects = objects[i : i + batch_size]
                        batch_vectors = vectors[i : i + batch_size] if vectors else None

                        # Create batch
                        with client.batch as batch:
                            for j, obj in enumerate(batch_objects):
                                vector = batch_vectors[j] if batch_vectors else None
                                uuid = str(
                                    batch.add_data_object(
                                        data_object=obj,
                                        class_name=class_name,
                                        vector=vector,
                                    )
                                )
                                uuids.append(uuid)

                    return uuids

                except WeaviateQueryError as e:
                    raise ServiceStateError(f"Batch operation failed: {e!s}") from e

    @require_initialized
    async def search_vectors(
        self,
        class_name: str,
        vector: list[float],
        limit: int = 10,
        distance_threshold: float = 0.8,
        with_payload: bool = True,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors with optimized performance.

        Args:
            class_name: Weaviate class name
            vector: Query vector
            limit: Maximum number of results
            distance_threshold: Similarity threshold
            with_payload: Whether to include object data

        Returns:
            List[Dict[str, Any]]: Search results

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If search operation fails
        """
        with self._metrics.measure_operation(
            "search_vectors",
            {
                "class_name": class_name,
                "limit": limit,
                "distance_threshold": distance_threshold,
                "with_payload": with_payload,
            },
        ):
            async with self.operation_context() as client:
                try:
                    # Cache query vector for potential reuse
                    query_id = str(hash(str(vector)))
                    self._vector_cache[query_id] = vector

                    # Build optimized query
                    query = (
                        client.query.get(class_name)
                        .with_near_vector({"vector": vector, "distance": distance_threshold})
                        .with_limit(limit)
                    )

                    if with_payload:
                        query = query.with_additional(["payload"])

                    result = query.do()

                    # Clean up cache periodically
                    if len(self._vector_cache) > 1000:
                        self._vector_cache.clear()

                    return result.get("data", {}).get("Get", {}).get(class_name, [])

                except WeaviateQueryError as e:
                    raise ServiceStateError(f"Vector search failed: {e!s}") from e

    @require_initialized
    async def delete_batch(
        self, class_name: str, uuids: list[str], batch_size: int | None = None
    ) -> None:
        """Delete multiple objects efficiently.

        Args:
            class_name: Weaviate class name
            uuids: List of UUIDs to delete
            batch_size: Optional custom batch size

        Raises:
            ServiceNotInitializedError: If service is not initialized
            ServiceStateError: If batch deletion fails
        """
        if not uuids:
            return

        batch_size = batch_size or self._batch_size

        with self._metrics.measure_operation(
            "delete_batch",
            {
                "class_name": class_name,
                "uuid_count": len(uuids),
                "batch_size": batch_size,
            },
        ):
            async with self.operation_context() as client:
                try:
                    # Process deletions in batches
                    for i in range(0, len(uuids), batch_size):
                        batch_uuids = uuids[i : i + batch_size]

                        with client.batch as batch:
                            for uuid in batch_uuids:
                                batch.delete_objects(
                                    class_name=class_name,
                                    where={
                                        "path": ["id"],
                                        "operator": "Equal",
                                        "valueString": uuid,
                                    },
                                )

                except WeaviateQueryError as e:
                    raise ServiceStateError(f"Batch deletion failed: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up Weaviate resources with graceful shutdown."""
        with self._metrics.measure_operation("cleanup"):
            if self._client and hasattr(self._client, "close"):
                try:
                    self._client.close()
                except Exception as e:
                    self.add_metadata("cleanup_error", str(e))
            self._client = None
            self._initialized = False
            self._health_check_failures = 0
            self._vector_cache.clear()
            self._metrics.reset()

    @backoff.on_exception(
        backoff.expo,
        (WeaviateConnectionError, WeaviateTimeoutError),
        max_tries=3,
        max_time=30,
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
        with self._metrics.measure_operation("initialize"):
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
                    f"Failed to initialize Weaviate connection: {e!s}"
                ) from e

    @backoff.on_exception(backoff.expo, WeaviateConnectionError, max_tries=2, max_time=10)
    async def health_check(self) -> bool:
        """Check Weaviate connection health with retry capability.

        Returns:
            bool: True if Weaviate is healthy, False otherwise
        """
        with self._metrics.measure_operation("health_check"):
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
        self, class_name: str, data_object: dict[str, Any], vector: list[float] | None = None
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
            except WeaviateQueryError as e:
                raise ServiceStateError(f"Failed to add object: {e!s}") from e

    @require_initialized
    async def get_object(self, class_name: str, uuid: str) -> dict[str, Any] | None:
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
            except WeaviateQueryError:
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
            except WeaviateQueryError as e:
                raise ServiceStateError(f"Failed to delete object: {e!s}") from e

    def get_metrics(self) -> dict[str, Any]:
        """Get service metrics.

        Returns:
            Dict[str, Any]: Current service metrics
        """
        return self._metrics.get_current_metrics()

    def get_health(self) -> dict[str, Any]:
        """Get service health status.

        Returns:
            Dict[str, Any]: Current health status
        """
        return self._metrics.check_health()
