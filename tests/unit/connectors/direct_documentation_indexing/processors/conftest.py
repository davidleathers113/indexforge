"""Shared fixtures for processor tests."""

import logging
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Set up logging for all tests."""
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def test_files_dir(tmp_path) -> Path:
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def cleanup_test_files(test_files_dir) -> Generator[None, None, None]:
    """Clean up test files after each test."""
    yield
    for file_path in test_files_dir.glob("*"):
        try:
            file_path.unlink()
        except Exception as e:
            logging.warning(f"Failed to delete {file_path}: {e}")
    try:
        test_files_dir.rmdir()
    except Exception as e:
        logging.warning(f"Failed to delete test directory: {e}")


@pytest.fixture
def sample_text() -> str:
    """Return sample text for test documents."""
    return "This is a sample text for testing document processing."
