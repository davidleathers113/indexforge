"""Tests for processing service input validation."""

import pytest

from src.services.ml.errors import ValidationError
from src.services.ml.implementations import ProcessingService
from src.services.ml.implementations.processing import ProcessingParameters


@pytest.fixture
async def initialized_service():
    """Create and initialize a processing service instance."""
    service = ProcessingService(
        ProcessingParameters(
            model_name="en_core_web_sm",
            min_text_length=10,
            max_text_length=1000000,
            min_words=3,
        )
    )
    await service.initialize()
    yield service
    await service.cleanup()


class TestInputValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_valid_chunk(self, initialized_service):
        """Test processing a valid chunk."""
        chunk = {
            "id": "test-1",
            "content": "This is a valid test chunk with sufficient content for processing.",
        }
        result = await initialized_service.process_chunk(chunk)
        assert result["id"] == chunk["id"]
        assert "results" in result

    @pytest.mark.asyncio
    async def test_missing_id(self, initialized_service):
        """Test chunk without ID."""
        chunk = {
            "content": "Test content",
        }
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunk(chunk)
        assert "id" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_missing_content(self, initialized_service):
        """Test chunk without content."""
        chunk = {
            "id": "test-1",
        }
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunk(chunk)
        assert "content" in str(exc.value).lower()


class TestContentValidation:
    """Tests for content validation."""

    @pytest.mark.asyncio
    async def test_content_too_short(self, initialized_service):
        """Test chunk with content below minimum length."""
        chunk = {
            "id": "test-1",
            "content": "Short",
        }
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunk(chunk)
        assert "length" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_content_too_long(self, initialized_service):
        """Test chunk with content above maximum length."""
        chunk = {
            "id": "test-1",
            "content": "x" * 1000001,
        }
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunk(chunk)
        assert "length" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_content_too_few_words(self, initialized_service):
        """Test chunk with insufficient word count."""
        chunk = {
            "id": "test-1",
            "content": "Two words",
        }
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunk(chunk)
        assert "words" in str(exc.value).lower()


class TestBatchValidation:
    """Tests for batch processing validation."""

    @pytest.mark.asyncio
    async def test_empty_batch(self, initialized_service):
        """Test processing empty batch."""
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunks([])
        assert "empty" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_chunk_in_batch(self, initialized_service):
        """Test batch with invalid chunk."""
        chunks = [
            {"id": "test-1", "content": "This is a valid test chunk with sufficient content."},
            {"id": "test-2"},  # Missing content
            {"id": "test-3", "content": "Another valid test chunk with good content."},
        ]
        with pytest.raises(ValidationError) as exc:
            await initialized_service.process_chunks(chunks)
        assert "test-2" in str(exc.value)

    @pytest.mark.asyncio
    async def test_valid_batch(self, initialized_service):
        """Test processing valid batch."""
        chunks = [
            {"id": "test-1", "content": "This is a valid test chunk with sufficient content."},
            {"id": "test-2", "content": "Another valid test chunk with good content."},
        ]
        results = await initialized_service.process_chunks(chunks)
        assert len(results) == 2
        assert all("results" in r for r in results)
        assert [r["id"] for r in results] == ["test-1", "test-2"]
