"""Key-related types and enums.

This module defines types specific to encryption key management,
including key types, metadata, and related enumerations.

Key Features:
    - Key type enumeration
    - Key metadata structures
    - Type-safe key operations
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from src.core.types.security.common import KeyID


class KeyType(Enum):
    """Types of encryption keys."""

    MASTER = auto()  # Master key used for key encryption
    DATA = auto()  # Keys used for data encryption
    METADATA = auto()  # Keys used for metadata encryption
    TEMPORARY = auto()  # Short-lived keys for temporary operations


@dataclass
class KeyMetadata:
    """Metadata for encryption keys.

    Attributes:
        key_id: Unique identifier for the key
        key_type: Type of encryption key
        created_at: Timestamp when key was created
        expires_at: Optional timestamp when key expires
        rotation_due: Optional timestamp when key should be rotated
    """

    key_id: KeyID
    key_type: KeyType
    created_at: float
    expires_at: Optional[float] = None
    rotation_due: Optional[float] = None
