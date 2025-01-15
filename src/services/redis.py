"""Redis service module.

This module provides a clean interface for interacting with Redis,
handling connection pooling and common operations.
"""

from typing import TYPE_CHECKING, Any, Optional

import redis
from redis import Redis
from redis.exceptions import RedisError

from src.core.interfaces import CacheService
from src.services.base import BaseService, ServiceInitializationError, ServiceNotInitializedError

if TYPE_CHECKING:
    from src.core.settings import Settings


class RedisService(CacheService, BaseService):
    """Redis service for managing Redis operations.

    This service handles Redis connection pooling and provides
    a clean interface for common Redis operations.
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize Redis service.

        Args:
            settings: Application settings
        """
        # Initialize base classes
        BaseService.__init__(self)
        CacheService.__init__(self, settings)
        self._settings = settings
        self._redis: Optional[Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection.

        Raises:
            ServiceInitializationError: If Redis connection fails
        """
        try:
            self._redis = redis.from_url(
                str(self._settings.redis_url),
                max_connections=self._settings.redis_pool_size,
                decode_responses=True,
            )
            # Verify connection
            await self.health_check()
            self._initialized = True
            self.add_metadata("redis_url", str(self._settings.redis_url))
            self.add_metadata("pool_size", self._settings.redis_pool_size)
        except RedisError as e:
            raise ServiceInitializationError(f"Failed to initialize Redis connection: {str(e)}")

    async def cleanup(self) -> None:
        """Clean up Redis resources."""
        if self._redis:
            self._redis.close()
            self._redis = None
        self._initialized = False

    async def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        try:
            if not self._redis:
                return False
            self._redis.ping()
            return True
        except RedisError:
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[str]: Value if exists, None otherwise

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        if not self.is_initialized or not self._redis:
            raise ServiceNotInitializedError("Redis service is not initialized")
        return self._redis.get(key)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in Redis.

        Args:
            key: Redis key
            value: Value to store
            expire: Optional expiration in seconds

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        if not self.is_initialized or not self._redis:
            raise ServiceNotInitializedError("Redis service is not initialized")
        self._redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        """Delete key from Redis.

        Args:
            key: Redis key to delete

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        if not self.is_initialized or not self._redis:
            raise ServiceNotInitializedError("Redis service is not initialized")
        self._redis.delete(key)
