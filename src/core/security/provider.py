"""Security service provider.

This module provides a centralized provider for security-related services,
managing their lifecycle and dependencies while ensuring proper initialization
and cleanup.
"""

# Standard library imports
import logging
from typing import Optional

# Core type imports
from src.core.types.security import SecurityError
from src.core.types.service import ServiceState

# Other internal imports
from src.services.base import BaseService

from .encryption import EncryptionConfig, EncryptionService
from .interfaces import EncryptionProtocol, KeyStorageProtocol
from .key_storage import FileKeyStorage, KeyStorageConfig

logger = logging.getLogger(__name__)


class SecurityServiceProvider(BaseService):
    """Provider for security-related services.

    This class manages the lifecycle and dependencies of security services,
    ensuring proper initialization order and cleanup.

    Attributes:
        encryption_config: Configuration for encryption service
        key_storage_config: Configuration for key storage service
    """

    def __init__(
        self,
        encryption_config: EncryptionConfig,
        key_storage_config: KeyStorageConfig,
    ) -> None:
        """Initialize the security service provider.

        Args:
            encryption_config: Configuration for encryption service
            key_storage_config: Configuration for key storage service
        """
        super().__init__()
        self.encryption_config = encryption_config
        self.key_storage_config = key_storage_config
        self._key_storage: Optional[KeyStorageProtocol] = None
        self._encryption: Optional[EncryptionProtocol] = None

    @property
    def key_storage(self) -> KeyStorageProtocol:
        """Get the key storage service.

        Returns:
            Initialized key storage service

        Raises:
            SecurityServiceError: If service is not initialized
        """
        if not self._key_storage:
            raise SecurityError("Key storage service not initialized")
        return self._key_storage

    @property
    def encryption(self) -> EncryptionProtocol:
        """Get the encryption service.

        Returns:
            Initialized encryption service

        Raises:
            SecurityServiceError: If service is not initialized
        """
        if not self._encryption:
            raise SecurityError("Encryption service not initialized")
        return self._encryption

    async def initialize(self) -> None:
        """Initialize security services.

        This method initializes services in the correct order:
        1. Key storage service
        2. Encryption service

        Raises:
            SecurityServiceError: If initialization fails
        """
        try:
            logger.info("Initializing security services")
            self._transition_state(ServiceState.INITIALIZING)

            # Initialize key storage first
            logger.debug("Initializing key storage service")
            self._key_storage = FileKeyStorage(self.key_storage_config)

            # Initialize encryption service
            logger.debug("Initializing encryption service")
            self._encryption = EncryptionService(
                self.encryption_config,
                self._key_storage,
            )

            self._transition_state(ServiceState.RUNNING)
            logger.info("Security services initialized successfully")

        except SecurityError as e:
            self._transition_state(ServiceState.ERROR)
            logger.exception("Security service initialization failed")
            raise SecurityError(f"Failed to initialize security services: {e}") from e

    async def cleanup(self) -> None:
        """Clean up security services.

        This method ensures proper cleanup of all managed services.
        """
        try:
            logger.info("Cleaning up security services")
            self._transition_state(ServiceState.STOPPING)

            # Add cleanup logic here if needed
            self._encryption = None
            self._key_storage = None

            self._transition_state(ServiceState.STOPPED)
            logger.info("Security services cleaned up successfully")

        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            logger.exception("Security service cleanup failed")
            raise SecurityError(f"Failed to clean up security services: {e}") from e

    async def health_check(self) -> bool:
        """Check health of security services.

        Returns:
            True if all services are healthy, False otherwise
        """
        try:
            self._check_running()
            # Add specific health checks here if needed
            return True
        except Exception as e:
            logger.error("Security services health check failed: %s", str(e))
            return False
