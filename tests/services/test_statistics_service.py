"""Tests for StatisticsService."""

from unittest.mock import AsyncMock

import pytest

from src.api.services.statistics_service import StatisticsService


@pytest.mark.asyncio
async def test_get_stats(
    statistics_service: StatisticsService,
    mock_repository: AsyncMock,
):
    """Test getting document statistics."""
    expected_stats = {
        "total_documents": 100,
        "total_size": 1024 * 1024,  # 1MB
        "document_types": {
            "pdf": 50,
            "docx": 30,
            "txt": 20,
        },
    }
    mock_repository.get_stats.return_value = expected_stats

    result = await statistics_service.get_stats()

    assert result == expected_stats
    mock_repository.get_stats.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats_empty(
    statistics_service: StatisticsService,
    mock_repository: AsyncMock,
):
    """Test getting statistics when no documents exist."""
    expected_stats = {
        "total_documents": 0,
        "total_size": 0,
        "document_types": {},
    }
    mock_repository.get_stats.return_value = expected_stats

    result = await statistics_service.get_stats()

    assert result == expected_stats
    assert result["total_documents"] == 0
    mock_repository.get_stats.assert_called_once()
