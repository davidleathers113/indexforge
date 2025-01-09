"""
Provides configuration and initialization for vector index operations.

This module contains classes for configuring and initializing the vector index
infrastructure, including the Weaviate client and Redis cache manager. It handles
all aspects of connection setup and configuration management.

The module includes:
- IndexConfig: Configuration dataclass for all index-related settings
- IndexInitializer: Handler for setting up client and cache connections

Example:
    ```python
    # Create configuration
    config = IndexConfig(
        client_url="http://localhost:8080",
        cache_host="localhost",
        cache_port=6379
    )

    # Initialize connections
    initializer = IndexInitializer(config)
    client, cache_manager = initializer.initialize()

    # Use the initialized components
    if client.is_ready():
        print("Vector index is ready")
    if cache_manager:
        print("Cache system is active")
    ```
"""

import logging
from dataclasses import dataclass
from typing import Optional

import weaviate

from src.utils.cache_manager import CacheManager


@dataclass
class IndexConfig:
    """
    Configuration settings for vector index and cache management.

    This dataclass encapsulates all configuration parameters needed for
    setting up the vector index and its associated cache system. It provides
    default values suitable for local development.

    Attributes:
        client_url: URL of the Weaviate instance (default: "http://localhost:8080")
        class_name: Name of the document class in Weaviate (default: "Document")
        batch_size: Size of batches for bulk operations (default: 100)
        cache_host: Redis cache host address (default: "localhost")
        cache_port: Redis cache port number (default: 6379)
        cache_ttl: Cache entry time-to-live in seconds (default: 24 hours)
        cache_prefix: Prefix for cache keys (default: "idx")

    Example:
        ```python
        # Default configuration for local development
        config = IndexConfig()

        # Custom configuration for production
        prod_config = IndexConfig(
            client_url="http://weaviate.prod:8080",
            batch_size=500,
            cache_host="redis.prod",
            cache_ttl=3600  # 1 hour
        )
        ```
    """

    client_url: str = "http://localhost:8080"
    class_name: str = "Document"
    batch_size: int = 100
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_ttl: int = 86400  # 24 hours
    cache_prefix: str = "idx"


class IndexInitializer:
    """
    Handles initialization and setup of vector index infrastructure.

    This class manages the creation and configuration of both the Weaviate
    client and the Redis cache manager. It includes error handling and
    logging for all initialization operations.

    The initializer ensures proper setup of:
    - Weaviate client connection
    - Redis cache connection (optional)
    - Connection error handling
    - Logging of initialization status

    Attributes:
        config: IndexConfig instance with configuration settings
        logger: Logger instance for tracking initialization

    Example:
        ```python
        config = IndexConfig(client_url="http://weaviate:8080")
        initializer = IndexInitializer(config)

        try:
            client, cache = initializer.initialize()
            print("Successfully initialized vector index")
        except ConnectionError as e:
            print(f"Failed to initialize: {e}")
        ```
    """

    def __init__(self, config: IndexConfig):
        """
        Initialize a new IndexInitializer instance.

        Creates an initializer with the specified configuration for setting
        up vector index infrastructure components.

        Args:
            config: Configuration settings for index initialization

        Raises:
            ValueError: If config contains invalid settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> tuple[weaviate.Client, Optional[CacheManager]]:
        """
        Initialize and configure all index infrastructure components.

        This method sets up both the Weaviate client and cache manager
        according to the configuration. The cache manager is optional and
        may be None if initialization fails.

        Returns:
            tuple: (weaviate_client, cache_manager)
                  cache_manager may be None if cache init fails

        Raises:
            ConnectionError: If Weaviate client connection fails
            Exception: If initialization fails for other reasons

        Example:
            ```python
            initializer = IndexInitializer(config)
            try:
                client, cache = initializer.initialize()
                if cache:
                    print("Full initialization successful")
                else:
                    print("Initialized without cache")
            except ConnectionError as e:
                print(f"Connection failed: {e}")
            ```
        """
        try:
            client = self._create_client()
            cache_manager = self._create_cache_manager()
            return client, cache_manager
        except Exception as e:
            msg = f"Failed to initialize index: {str(e)}"
            self.logger.error(msg)
            raise ConnectionError(msg)

    def _create_client(self) -> weaviate.Client:
        """
        Create and configure the Weaviate client.

        Internal method that handles the creation of the Weaviate client
        instance with proper error handling and logging.

        Returns:
            weaviate.Client: Configured Weaviate client instance

        Raises:
            ConnectionError: If client creation or connection fails

        Note:
            This is an internal method and should not be called directly.
            Use initialize() instead.
        """
        try:
            return weaviate.Client(self.config.client_url)
        except Exception as e:
            msg = f"Failed to connect to Weaviate: {str(e)}"
            self.logger.error(msg)
            raise ConnectionError(msg)

    def _create_cache_manager(self) -> Optional[CacheManager]:
        """
        Create and configure the Redis cache manager.

        Internal method that handles the creation of the cache manager
        instance. Failure to create the cache manager is logged but
        does not prevent system operation.

        Returns:
            Optional[CacheManager]: Configured cache manager or None if
                                  creation fails

        Note:
            This is an internal method and should not be called directly.
            Use initialize() instead.
        """
        try:
            return CacheManager(
                host=self.config.cache_host,
                port=self.config.cache_port,
                prefix=self.config.cache_prefix,
                default_ttl=self.config.cache_ttl,
            )
        except Exception as e:
            self.logger.warning(f"Failed to initialize cache manager: {str(e)}")
            return None
