"""Common security types and constants.

This module defines shared types and constants used across security services,
providing a centralized location for type definitions and preventing
circular dependencies.

Key Features:
    - Security-related type definitions
    - Key type enumerations
    - Common security constants
"""

from typing import NewType

# Type definitions
KeyID = NewType("KeyID", str)
EncryptedData = NewType("EncryptedData", bytes)
KeyData = NewType("KeyData", bytes)

# Constants
DEFAULT_KEY_EXPIRY_DAYS = 90
MINIMUM_KEY_LENGTH = 32
ROTATION_WARNING_DAYS = 7
