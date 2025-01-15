"""Factory for creating service instances."""

from typing import Type, TypeVar

from src.core.interfaces import CacheService, VectorService
from src.core.settings import Settings
from src.services.base import BaseService, ServiceInitializationError
from src.services.redis import RedisService
from src.services.weaviate import WeaviateClient

T = TypeVar("T", bound=BaseService)


class ServiceFactory:
    """Factory for creating service instances.

    This factory ensures proper initialization of services and provides
    a clean interface for service creation with dependency injection.
    """

    @classmethod
    async def create_service(cls, settings: Settings, service_type: Type[T], **kwargs) -> T:
        """Create and initialize a service instance.

        Args:
            settings: Application settings
            service_type: Type of service to create
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            An initialized service instance

        Raises:
            ServiceInitializationError: If service initialization fails
        """
        try:
            service = service_type(settings, **kwargs)
            await service.initialize()
            return service
        except Exception as e:
            raise ServiceInitializationError(
                f"Failed to initialize {service_type.__name__}: {str(e)}"
            )

    @classmethod
    async def create_cache_service(
        cls, settings: Settings, service_type: Type[CacheService] = RedisService, **kwargs
    ) -> CacheService:
        """Create a cache service instance.

        Args:
            settings: Application settings
            service_type: Type of cache service to create (defaults to RedisService)
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            An initialized cache service
        """
        return await cls.create_service(settings, service_type, **kwargs)

    @classmethod
    async def create_vector_service(
        cls, settings: Settings, service_type: Type[VectorService] = WeaviateClient, **kwargs
    ) -> VectorService:
        """Create a vector service instance.

        Args:
            settings: Application settings
            service_type: Type of vector service to create (defaults to WeaviateClient)
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            An initialized vector service
        """
        return await cls.create_service(settings, service_type, **kwargs)
