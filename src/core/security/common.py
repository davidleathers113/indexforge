"""Common types and utilities for security services.

This module contains shared types, constants, and utility functions used
across security services to prevent circular dependencies.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import NewType, Optional

# Type definitions
KeyID = NewType("KeyID", str)
EncryptedData = NewType("EncryptedData", bytes)
KeyData = NewType("KeyData", bytes)


class KeyType(Enum):
    """Types of encryption keys."""

    MASTER = auto()
    DATA = auto()
    METADATA = auto()
    TEMPORARY = auto()


@dataclass
class KeyMetadata:
    """Metadata for encryption keys."""

    key_id: KeyID
    key_type: KeyType
    created_at: float
    expires_at: Optional[float] = None
    rotation_due: Optional[float] = None


class SecurityError(Exception):
    """Base class for security-related errors."""

    pass


class KeyNotFoundError(SecurityError):
    """Raised when a key cannot be found."""

    pass


class KeyRotationError(SecurityError):
    """Raised when key rotation fails."""

    pass


class EncryptionError(SecurityError):
    """Raised when encryption/decryption fails."""

    pass


# Constants
DEFAULT_KEY_EXPIRY_DAYS = 90
MINIMUM_KEY_LENGTH = 32
ROTATION_WARNING_DAYS = 7
