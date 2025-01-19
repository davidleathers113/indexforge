"""Test fixtures for embedding tests."""

from unittest.mock import Mock

import pytest

from src.core import Chunk
from src.core.settings import Settings
from src.ml.embeddings.config import GeneratorConfig, ValidatorConfig
from src.ml.embeddings.service import EmbeddingService


@pytest.fixture
def validator_config() -> ValidatorConfig:
    """Provide test validator configuration."""
    return ValidatorConfig(min_words=2, min_size=10, max_size=1000)


@pytest.fixture
def generator_config() -> GeneratorConfig:
    """Provide test generator configuration."""
    return GeneratorConfig(model_name="test-model", batch_size=2, device="cpu")


@pytest.fixture
def settings(generator_config: GeneratorConfig) -> Settings:
    """Provide test settings."""
    settings = Mock(spec=Settings)
    settings.embedding_model = generator_config.model_name
    settings.batch_size = generator_config.batch_size
    return settings


@pytest.fixture
async def embedding_service(settings: Settings) -> EmbeddingService:
    """Provide test embedding service.

    This fixture creates and initializes an EmbeddingService instance
    for testing, cleaning up after the test completes.
    """
    service = EmbeddingService(settings)
    await service.initialize()
    yield service
    await service.cleanup()


@pytest.fixture
def valid_chunk() -> Chunk:
    """Provide a valid test chunk."""
    return Chunk(
        id="test-chunk", content="This is a valid test chunk with sufficient content.", metadata={}
    )


@pytest.fixture
def invalid_chunk() -> Chunk:
    """Provide an invalid test chunk."""
    return Chunk(id="invalid-chunk", content="", metadata={})  # Empty content
