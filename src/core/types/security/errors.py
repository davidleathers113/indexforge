"""Security error types.

This module defines error types specific to security operations,
providing a consistent way to handle and report security-related errors.

Key Features:
    - Security error hierarchy
    - Key management errors
    - Encryption errors
"""

from typing import Optional

from src.core.types.service import ServiceError


class SecurityError(ServiceError):
    """Base class for security-related errors."""

    def __init__(self, message: str, service_name: Optional[str] = None) -> None:
        """Initialize security error.

        Args:
            message: Error message
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)


class KeyNotFoundError(SecurityError):
    """Raised when a key cannot be found."""

    def __init__(self, key_id: str, service_name: Optional[str] = None) -> None:
        """Initialize key not found error.

        Args:
            key_id: ID of key that was not found
            service_name: Name of service that raised the error
        """
        super().__init__(f"Key not found: {key_id}", service_name)
        self.key_id = key_id


class KeyRotationError(SecurityError):
    """Raised when key rotation fails."""

    def __init__(
        self,
        message: str,
        key_id: str,
        reason: str,
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize key rotation error.

        Args:
            message: Error message
            key_id: ID of key that failed to rotate
            reason: Reason for rotation failure
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.key_id = key_id
        self.reason = reason


class EncryptionError(SecurityError):
    """Raised when encryption/decryption fails."""

    def __init__(
        self,
        message: str,
        operation: str,
        reason: str,
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize encryption error.

        Args:
            message: Error message
            operation: Name of operation that failed (encrypt/decrypt)
            reason: Reason for operation failure
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.operation = operation
        self.reason = reason
