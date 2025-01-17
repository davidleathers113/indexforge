"""Tests for secure storage metadata handler.

This module contains tests for the SecureStorageMetadata and MetadataHandler classes,
ensuring proper handling of encryption metadata for secure document storage.
"""

import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.core.security.encryption import EncryptedData
from src.services.storage.secure_metadata import MetadataHandler, SecureStorageMetadata

logger = logging.getLogger(__name__)


@pytest.fixture
def metadata_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for metadata storage.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path to temporary metadata directory
    """
    metadata_path = tmp_path / "metadata"
    metadata_path.mkdir()
    return metadata_path


@pytest.fixture
def encrypted_data() -> EncryptedData:
    """Create sample encrypted data for testing.

    Returns:
        Sample encrypted data
    """
    return EncryptedData(ciphertext=b"encrypted_content", nonce=b"test_nonce", tag=b"test_tag")


@pytest.fixture
def metadata(encrypted_data: EncryptedData) -> SecureStorageMetadata:
    """Create sample metadata for testing.

    Args:
        encrypted_data: Sample encrypted data

    Returns:
        Sample metadata
    """
    return SecureStorageMetadata(version=1, encryption_data=encrypted_data)


def test_metadata_validation():
    """Test metadata model validation."""
    # Valid metadata
    metadata = SecureStorageMetadata(
        version=1, encryption_data=EncryptedData(ciphertext=b"test", nonce=b"nonce", tag=b"tag")
    )
    assert metadata.version == 1
    assert metadata.encryption_data.ciphertext == b"test"

    # Invalid version
    with pytest.raises(ValidationError):
        SecureStorageMetadata(
            version=0, encryption_data=EncryptedData(ciphertext=b"test", nonce=b"nonce", tag=b"tag")
        )


def test_metadata_handler_initialization(metadata_dir: Path):
    """Test metadata handler initialization.

    Args:
        metadata_dir: Temporary metadata directory
    """
    handler = MetadataHandler(metadata_dir)
    assert handler._metadata_dir == metadata_dir
    assert handler._metadata == {}
    assert metadata_dir.exists()


def test_save_and_get_metadata(metadata_dir: Path, metadata: SecureStorageMetadata):
    """Test saving and retrieving metadata.

    Args:
        metadata_dir: Temporary metadata directory
        metadata: Sample metadata
    """
    handler = MetadataHandler(metadata_dir)
    doc_id = uuid4()

    # Save metadata
    handler.save(doc_id, metadata)

    # Verify file exists
    metadata_file = metadata_dir / f"{doc_id}.meta.json"
    assert metadata_file.exists()

    # Verify content
    saved_metadata = handler.get(doc_id)
    assert saved_metadata is not None
    assert saved_metadata.version == metadata.version
    assert saved_metadata.encryption_data == metadata.encryption_data


def test_delete_metadata(metadata_dir: Path, metadata: SecureStorageMetadata):
    """Test deleting metadata.

    Args:
        metadata_dir: Temporary metadata directory
        metadata: Sample metadata
    """
    handler = MetadataHandler(metadata_dir)
    doc_id = uuid4()

    # Save and verify
    handler.save(doc_id, metadata)
    assert handler.get(doc_id) is not None

    # Delete and verify
    handler.delete(doc_id)
    assert handler.get(doc_id) is None
    metadata_file = metadata_dir / f"{doc_id}.meta.json"
    assert not metadata_file.exists()


def test_load_all_metadata(metadata_dir: Path, metadata: SecureStorageMetadata):
    """Test loading all metadata from disk.

    Args:
        metadata_dir: Temporary metadata directory
        metadata: Sample metadata
    """
    # Create multiple metadata files
    doc_ids = [uuid4() for _ in range(3)]
    for doc_id in doc_ids:
        metadata_file = metadata_dir / f"{doc_id}.meta.json"
        metadata_file.write_text(json.dumps(metadata.dict()))

    # Initialize handler and verify loading
    handler = MetadataHandler(metadata_dir)
    for doc_id in doc_ids:
        assert handler.get(doc_id) is not None


def test_handle_invalid_metadata_file(metadata_dir: Path):
    """Test handling of invalid metadata files.

    Args:
        metadata_dir: Temporary metadata directory
    """
    # Create invalid metadata file
    doc_id = uuid4()
    metadata_file = metadata_dir / f"{doc_id}.meta.json"
    metadata_file.write_text("invalid json")

    # Initialize handler and verify error handling
    handler = MetadataHandler(metadata_dir)
    assert handler.get(doc_id) is None


def test_atomic_metadata_save(metadata_dir: Path, metadata: SecureStorageMetadata):
    """Test atomic metadata save operation.

    Args:
        metadata_dir: Temporary metadata directory
        metadata: Sample metadata
    """
    handler = MetadataHandler(metadata_dir)
    doc_id = uuid4()

    # Verify temp file handling
    temp_path = metadata_dir / f"{doc_id}.meta.json.tmp"
    handler.save(doc_id, metadata)
    assert not temp_path.exists()

    # Verify final file exists
    metadata_file = metadata_dir / f"{doc_id}.meta.json"
    assert metadata_file.exists()


def test_handle_save_failure(metadata_dir: Path, metadata: SecureStorageMetadata, monkeypatch):
    """Test handling of save operation failures.

    Args:
        metadata_dir: Temporary metadata directory
        metadata: Sample metadata
        monkeypatch: Pytest monkeypatch fixture
    """

    def mock_dump(*args, **kwargs):
        raise IOError("Simulated write failure")

    monkeypatch.setattr(json, "dump", mock_dump)

    handler = MetadataHandler(metadata_dir)
    doc_id = uuid4()

    # Verify error handling
    with pytest.raises(Exception):
        handler.save(doc_id, metadata)

    # Verify no temp file remains
    temp_path = metadata_dir / f"{doc_id}.meta.json.tmp"
    assert not temp_path.exists()

    # Verify no metadata file was created
    metadata_file = metadata_dir / f"{doc_id}.meta.json"
    assert not metadata_file.exists()
