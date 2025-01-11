"""Tests for FileUploadService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from src.api.services.file_upload_service import FileUploadService


@pytest.mark.asyncio
async def test_process_upload_success(
    file_upload_service: FileUploadService,
    test_file: UploadFile,
    mock_repository: AsyncMock,
    mock_virus_scan: AsyncMock,
    mock_connector: MagicMock,
):
    """Test successful file upload processing."""
    response = await file_upload_service.process_upload(test_file)

    assert response.status == "success"
    assert response.file_name == "test.txt"
    assert response.document_id == "test-doc-id"

    mock_virus_scan.scan_file.assert_called_once_with(test_file)
    mock_connector.process_file.assert_called_once()
    mock_repository.index_single_document.assert_called_once()


@pytest.mark.asyncio
async def test_process_upload_virus_scan_failure(
    file_upload_service: FileUploadService,
    test_file: UploadFile,
    mock_virus_scan: AsyncMock,
):
    """Test file upload with virus scan failure."""
    mock_virus_scan.scan_file.return_value = False

    response = await file_upload_service.process_upload(test_file)

    assert response.status == "error"
    assert "security scan" in response.message.lower()
    mock_virus_scan.scan_file.assert_called_once_with(test_file)


@pytest.mark.asyncio
async def test_process_upload_unsupported_file_type(
    file_upload_service: FileUploadService,
    mock_connector: MagicMock,
):
    """Test file upload with unsupported file type."""
    file = UploadFile(filename="test.xyz")
    mock_connector.processors = {}

    response = await file_upload_service.process_upload(file)

    assert response.status == "error"
    assert "unsupported file type" in response.message.lower()


@pytest.mark.asyncio
async def test_process_upload_processing_error(
    file_upload_service: FileUploadService,
    test_file: UploadFile,
    mock_connector: MagicMock,
):
    """Test file upload with processing error."""
    mock_connector.process_file.return_value = {
        "status": "error",
        "error": "Processing failed",
    }

    response = await file_upload_service.process_upload(test_file)

    assert response.status == "error"
    assert "processing failed" in response.message.lower()


@pytest.mark.asyncio
async def test_process_batch_upload(
    file_upload_service: FileUploadService,
    test_file: UploadFile,
):
    """Test batch file upload processing."""
    files = [test_file, test_file]  # Use the same file twice for testing
    responses = await file_upload_service.process_batch_upload(files)

    assert len(responses) == 2
    assert all(r.status == "success" for r in responses)
    assert all(r.document_id == "test-doc-id" for r in responses)
