"""Tests for processing service error recovery."""

import pytest

from src.services.ml.errors import ProcessingError, ServiceInitializationError
from src.services.ml.implementations import ProcessingService
from src.services.ml.implementations.processing import ProcessingParameters


@pytest.fixture
def processing_service():
    """Create a processing service instance for testing."""
    return ProcessingService(
        ProcessingParameters(
            model_name="en_core_web_sm",
            min_text_length=10,
            max_text_length=1000000,
            min_words=3,
        )
    )


class TestModelFailures:
    """Tests for model loading and processing failures."""

    @pytest.mark.asyncio
    async def test_model_load_failure(self, processing_service, monkeypatch):
        """Test recovery from model load failure."""

        def mock_load(*args, **kwargs):
            raise RuntimeError("Failed to load model")

        monkeypatch.setattr("spacy.load", mock_load)

        # First attempt should fail
        with pytest.raises(ServiceInitializationError):
            await processing_service.initialize()

        # Service should be in clean state
        assert not processing_service.is_initialized
        assert not processing_service.is_running

        # Restore model loading and retry
        monkeypatch.undo()
        await processing_service.initialize()
        assert processing_service.is_initialized
        assert processing_service.is_running

    @pytest.mark.asyncio
    async def test_processing_failure_recovery(self, processing_service, monkeypatch):
        """Test recovery from processing failure."""
        await processing_service.initialize()

        # Mock processing to fail
        def mock_process(*args, **kwargs):
            raise RuntimeError("Processing failed")

        monkeypatch.setattr(processing_service._model.model, "pipe", mock_process)

        # Processing should fail but service should remain operational
        chunk = {
            "id": "test-1",
            "content": "This is a test chunk that will fail processing.",
        }
        with pytest.raises(ProcessingError):
            await processing_service.process_chunk(chunk)

        assert processing_service.is_initialized
        assert processing_service.is_running

        # Restore processing and retry
        monkeypatch.undo()
        result = await processing_service.process_chunk(chunk)
        assert result["id"] == chunk["id"]
        assert "results" in result


class TestResourceCleanup:
    """Tests for resource cleanup after failures."""

    @pytest.mark.asyncio
    async def test_cleanup_after_processing_error(self, processing_service):
        """Test cleanup after processing error."""
        await processing_service.initialize()

        # Simulate processing error
        chunk = {
            "id": "test-1",
            "content": "x" * 1000001,  # Too long, will fail validation
        }
        with pytest.raises(ProcessingError):
            await processing_service.process_chunk(chunk)

        # Cleanup should succeed
        await processing_service.cleanup()
        assert not processing_service.is_initialized
        assert not processing_service.is_running

    @pytest.mark.asyncio
    async def test_cleanup_after_batch_failure(self, processing_service):
        """Test cleanup after batch processing failure."""
        await processing_service.initialize()

        # Simulate batch processing error
        chunks = [
            {"id": "test-1", "content": "Valid chunk content."},
            {"id": "test-2"},  # Invalid chunk
        ]
        with pytest.raises(ProcessingError):
            await processing_service.process_chunks(chunks)

        # Cleanup should succeed
        await processing_service.cleanup()
        assert not processing_service.is_initialized
        assert not processing_service.is_running


class TestGracefulDegradation:
    """Tests for graceful degradation scenarios."""

    @pytest.mark.asyncio
    async def test_partial_pipeline_failure(self, processing_service, monkeypatch):
        """Test handling of partial pipeline failures."""
        await processing_service.initialize()

        # Mock one pipeline component to fail
        def mock_component(*args, **kwargs):
            raise RuntimeError("Component failed")

        # Add failing component to pipeline
        processing_service._model.model.add_pipe("failing", before="ner")
        monkeypatch.setattr(
            processing_service._model.model.get_pipe("failing"), "__call__", mock_component
        )

        # Processing should continue with degraded results
        chunk = {
            "id": "test-1",
            "content": "This is a test chunk for degraded processing.",
        }
        result = await processing_service.process_chunk(chunk)
        assert result["id"] == chunk["id"]
        assert "results" in result  # Basic results should still be present

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, processing_service):
        """Test handling of memory pressure scenarios."""
        await processing_service.initialize()

        # Process large batch to simulate memory pressure
        chunks = [
            {
                "id": f"test-{i}",
                "content": f"Test content {i} " * 1000,  # Large but valid content
            }
            for i in range(10)
        ]

        # Should process without errors, potentially with degraded performance
        results = await processing_service.process_chunks(chunks)
        assert len(results) == len(chunks)
        assert all("results" in r for r in results)
