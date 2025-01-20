"""Tests for the key storage service."""

# Standard library imports
import datetime
import os
from unittest import mock

# Third party imports
import pytest

# Other internal imports
from src.core.security.key_storage import FileKeyStorage, KeyStorageConfig

# Core type imports
from src.core.types.security import (
    DEFAULT_KEY_EXPIRY_DAYS,
    KeyMetadata,
    KeyNotFoundError,
    KeyType,
    SecurityError,
)
from src.core.utils.time import utc_now

# Test fixtures and helper functions below
