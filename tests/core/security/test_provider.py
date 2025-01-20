"""Tests for the security service provider."""

import datetime
import unittest
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from src.core.security.encryption import EncryptionConfig
from src.core.security.key_storage import KeyStorageConfig
from src.core.security.provider import SecurityServiceProvider
from src.core.types.security import DEFAULT_KEY_EXPIRY_DAYS, KeyMetadata, KeyType, SecurityError
from src.core.types.service import ServiceState

# Test fixtures and helper functions below
