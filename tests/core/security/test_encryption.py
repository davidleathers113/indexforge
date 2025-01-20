"""Tests for the encryption service."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pytest
from cryptography.fernet import Fernet

from src.core.security.common import create_encryption_key, get_active_key, rotate_encryption_keys
from src.core.security.encryption import (
    EncryptionConfig,
    EncryptionService,
    decrypt_data,
    encrypt_data,
    generate_key,
)
from src.core.security.key_storage import FileKeyStorage, KeyStorageConfig
from src.core.types.security import (
    DEFAULT_KEY_EXPIRY_DAYS,
    EncryptionError,
    KeyMetadata,
    KeyNotFoundError,
    KeyRotationError,
    KeyStatus,
    KeyType,
)

# Test fixtures and helper functions below
