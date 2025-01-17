"""Security management for IndexForge.

This package provides functionality for:
- Authentication and authorization
- Encryption and key management
- Security policy enforcement
"""

from .auth import AuthenticationError, AuthenticationManager, InvalidCredentialsError
from .authorization import AuthorizationManager
from .encryption import EncryptionManager
from .key_storage import FileKeyStorage, KeyStorageError


__all__ = [
    # Authentication
    "AuthenticationError",
    "AuthenticationManager",
    "InvalidCredentialsError",
    # Authorization
    "AuthorizationManager",
    # Encryption
    "EncryptionManager",
    # Key Management
    "FileKeyStorage",
    "KeyStorageError",
]
