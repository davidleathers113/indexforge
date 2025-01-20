"""Security types package.

This package provides types for security operations, including:
- Key types and metadata
- Security error types
- Common security constants
"""

from .common import (
    DEFAULT_KEY_EXPIRY_DAYS,
    MINIMUM_KEY_LENGTH,
    ROTATION_WARNING_DAYS,
    EncryptedData,
    KeyData,
    KeyID,
)
from .errors import EncryptionError, KeyNotFoundError, KeyRotationError, SecurityError
from .keys import KeyMetadata, KeyType

__all__ = [
    # Common
    "KeyID",
    "KeyData",
    "EncryptedData",
    "DEFAULT_KEY_EXPIRY_DAYS",
    "MINIMUM_KEY_LENGTH",
    "ROTATION_WARNING_DAYS",
    # Errors
    "SecurityError",
    "KeyNotFoundError",
    "KeyRotationError",
    "EncryptionError",
    # Keys
    "KeyType",
    "KeyMetadata",
]
