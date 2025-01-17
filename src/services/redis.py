"""Redis service module with advanced caching strategies.

This module provides a clean interface for interacting with Redis,
handling connection pooling, pipelining, and advanced caching operations.
"""

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Union

import redis
from redis import Redis
from redis.client import Pipeline
from redis.exceptions import RedisError

from src.core.interfaces import CacheService
from src.core.metrics import ServiceMetricsCollector
from src.services.base import BaseService, ServiceInitializationError, ServiceNotInitializedError


if TYPE_CHECKING:
    from src.core.settings import Settings


CacheValue = Union[str, int, float, bytes, list[Any], dict[str, Any]]
PipelineOperation = tuple[str, str, list[Any]]  # command, key, args


class RedisService(CacheService, BaseService):
    """Redis service for managing Redis operations with advanced features."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize Redis service with advanced configuration."""
        BaseService.__init__(self)
        CacheService.__init__(self, settings)
        self._settings = settings
        self._redis: Redis | None = None
        self._pipeline_batch_size = 1000
        self._default_ttl = 3600  # 1 hour
        self._metrics = ServiceMetricsCollector(
            service_name="redis",
            max_history=5000,
            memory_threshold_mb=500,
        )

    def _validate_connection(self) -> None:
        """Validate Redis connection status.

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        if not self.is_initialized or not self._redis:
            raise ServiceNotInitializedError("Redis service is not initialized")

    async def initialize(self) -> None:
        """Initialize Redis connection with advanced configuration.

        Raises:
            ServiceInitializationError: If Redis connection fails
        """
        with self._metrics.measure_operation("initialize"):
            try:
                self._redis = redis.from_url(
                    str(self._settings.redis_url),
                    max_connections=self._settings.redis_pool_size,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                )
                # Verify connection
                await self.health_check()
                self._initialized = True
                self.add_metadata("redis_url", str(self._settings.redis_url))
                self.add_metadata("pool_size", self._settings.redis_pool_size)
            except RedisError as e:
                raise ServiceInitializationError(f"Failed to initialize Redis connection: {e!s}")

    async def cleanup(self) -> None:
        """Clean up Redis resources with proper connection handling."""
        with self._metrics.measure_operation("cleanup"):
            if self._redis:
                try:
                    await self.flush_all()  # Optional: clear all data
                except RedisError:
                    pass  # Ignore cleanup errors
                self._redis.close()
                self._redis = None
            self._initialized = False
            self._metrics.reset()

    async def health_check(self) -> bool:
        """Check Redis connection health with timeout handling.

        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        with self._metrics.measure_operation("health_check"):
            try:
                if not self._redis:
                    return False
                self._redis.ping()
                return True
            except RedisError:
                return False

    async def get(self, key: str) -> CacheValue | None:
        """Get value from Redis with type handling.

        Args:
            key: Redis key

        Returns:
            Optional[CacheValue]: Value if exists, None otherwise

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation("get", {"key": key}):
            try:
                value = self._redis.get(key)  # type: ignore
                if value and value.startswith(("list:", "dict:")):
                    import json

                    prefix, data = value.split(":", 1)
                    return json.loads(data)
                return value
            except RedisError:
                return None

    async def set(
        self,
        key: str,
        value: CacheValue,
        expire: int | timedelta | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in Redis with advanced options.

        Args:
            key: Redis key
            value: Value to store
            expire: Optional expiration (seconds or timedelta)
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            bool: True if set was successful

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation(
            "set",
            {
                "key": key,
                "expire": str(expire) if expire else None,
                "nx": nx,
                "xx": xx,
            },
        ):
            try:
                # Handle complex types
                if isinstance(value, (list, dict)):
                    import json

                    prefix = "list:" if isinstance(value, list) else "dict:"
                    value = f"{prefix}{json.dumps(value)}"

                # Convert timedelta to seconds
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())

                return bool(
                    self._redis.set(  # type: ignore
                        key,
                        value,
                        ex=expire,
                        nx=nx,
                        xx=xx,
                    )
                )
            except RedisError:
                return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis with result checking.

        Args:
            key: Redis key to delete

        Returns:
            bool: True if key was deleted

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation("delete", {"key": key}):
            try:
                return bool(self._redis.delete(key))  # type: ignore
            except RedisError:
                return False

    async def pipeline_execute(
        self,
        operations: list[PipelineOperation],
        transaction: bool = True,
        raise_on_error: bool = False,
    ) -> list[Any]:
        """Execute multiple operations in a pipeline.

        Args:
            operations: List of (command, key, args) tuples
            transaction: Whether to execute as transaction
            raise_on_error: Whether to raise on operation errors

        Returns:
            List[Any]: Operation results

        Raises:
            ServiceNotInitializedError: If service is not initialized
            RedisError: If pipeline execution fails and raise_on_error is True
        """
        self._validate_connection()
        with self._metrics.measure_operation(
            "pipeline_execute",
            {
                "operation_count": len(operations),
                "transaction": transaction,
                "raise_on_error": raise_on_error,
            },
        ):
            results = []

            try:
                # Process in batches to avoid memory issues
                for i in range(0, len(operations), self._pipeline_batch_size):
                    batch = operations[i : i + self._pipeline_batch_size]
                    pipe: Pipeline = self._redis.pipeline(transaction=transaction)  # type: ignore

                    # Add operations to pipeline
                    for cmd, key, args in batch:
                        getattr(pipe, cmd)(key, *args)

                    # Execute batch
                    batch_results = pipe.execute(raise_on_error=raise_on_error)
                    results.extend(batch_results)

                return results

            except RedisError:
                if raise_on_error:
                    raise
                return [None] * len(operations)

    async def flush_all(self) -> bool:
        """Clear all data from Redis.

        Returns:
            bool: True if successful

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation("flush_all"):
            try:
                self._redis.flushall()  # type: ignore
                return True
            except RedisError:
                return False

    async def get_many(self, keys: list[str]) -> dict[str, CacheValue | None]:
        """Get multiple values efficiently.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dict[str, Optional[CacheValue]]: Map of key to value

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation("get_many", {"key_count": len(keys)}):
            try:
                pipe: Pipeline = self._redis.pipeline(transaction=True)  # type: ignore
                for key in keys:
                    pipe.get(key)
                values = pipe.execute()
                return dict(zip(keys, values, strict=False))
            except RedisError:
                return dict.fromkeys(keys)

    async def set_many(
        self,
        items: dict[str, CacheValue],
        expire: int | timedelta | None = None,
    ) -> bool:
        """Set multiple key-value pairs efficiently.

        Args:
            items: Dictionary of key-value pairs to set
            expire: Optional expiration for all items

        Returns:
            bool: True if all operations successful

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._validate_connection()
        with self._metrics.measure_operation(
            "set_many",
            {
                "key_count": len(items),
                "expire": str(expire) if expire else None,
            },
        ):
            try:
                pipe: Pipeline = self._redis.pipeline(transaction=True)  # type: ignore

                # Convert timedelta to seconds
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())

                for key, value in items.items():
                    # Handle complex types
                    if isinstance(value, (list, dict)):
                        import json

                        prefix = "list:" if isinstance(value, list) else "dict:"
                        value = f"{prefix}{json.dumps(value)}"

                    pipe.set(key, value, ex=expire)

                results = pipe.execute()
                return all(results)
            except RedisError:
                return False

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
