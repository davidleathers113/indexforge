"""Tests for chunking configuration validation and error handling."""
import pytest

from src.utils.chunking import ChunkingConfig


def test_default_config_is_valid():
    """Test that default configuration is valid."""
    config = ChunkingConfig()
    assert config.chunk_size == 512
    assert config.chunk_overlap == 50
    assert not config.use_advanced_chunking
    assert config.min_chunk_size == 25
    assert config.max_chunk_size == 100


def test_invalid_chunk_size():
    """Test that invalid chunk sizes raise appropriate errors."""
    with pytest.raises(ValueError, match='chunk_size must be positive'):
        ChunkingConfig(chunk_size=0)
    with pytest.raises(ValueError, match='chunk_size must be positive'):
        ChunkingConfig(chunk_size=-100)


def test_invalid_chunk_overlap():
    """Test that invalid chunk overlap values raise appropriate errors."""
    with pytest.raises(ValueError, match='chunk_overlap must be non-negative'):
        ChunkingConfig(chunk_size=100, chunk_overlap=-1)
    with pytest.raises(ValueError, match='chunk_overlap must be less than chunk_size'):
        ChunkingConfig(chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError, match='chunk_overlap must be less than chunk_size'):
        ChunkingConfig(chunk_size=100, chunk_overlap=150)


def test_invalid_min_max_chunk_size():
    """Test validation of min/max chunk size relationships."""
    with pytest.raises(ValueError, match='min_chunk_size must be positive'):
        ChunkingConfig(min_chunk_size=0)
    with pytest.raises(ValueError, match='min_chunk_size must be positive'):
        ChunkingConfig(min_chunk_size=-10)
    with pytest.raises(ValueError, match='max_chunk_size must be greater than min_chunk_size'):
        ChunkingConfig(min_chunk_size=100, max_chunk_size=50)
    with pytest.raises(ValueError, match='max_chunk_size must be greater than min_chunk_size'):
        ChunkingConfig(min_chunk_size=100, max_chunk_size=100)


def test_model_name_validation():
    """Test model name handling."""
    config = ChunkingConfig(model_name='text-embedding-3-small')
    assert config.model_name == 'text-embedding-3-small'
    config = ChunkingConfig(model_name=None)
    assert config.model_name is None


def test_advanced_chunking_parameter():
    """Test advanced chunking parameter behavior."""
    config = ChunkingConfig(use_advanced_chunking=True)
    assert config.use_advanced_chunking
    config = ChunkingConfig(use_advanced_chunking=False)
    assert not config.use_advanced_chunking
    config = ChunkingConfig()
    assert not config.use_advanced_chunking


def test_chunk_size_relationships():
    """Test relationships between different size parameters."""
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=50, min_chunk_size=100, max_chunk_size=200)
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=1000, min_chunk_size=50, max_chunk_size=500)


def test_parameter_types():
    """Test that parameters are of correct type."""
    with pytest.raises(TypeError):
        ChunkingConfig(chunk_size='100')
    with pytest.raises(TypeError):
        ChunkingConfig(chunk_overlap=10.5)
    with pytest.raises(TypeError):
        ChunkingConfig(use_advanced_chunking='true')
    with pytest.raises(TypeError):
        ChunkingConfig(min_chunk_size=25.5)
    with pytest.raises(TypeError):
        ChunkingConfig(max_chunk_size=100.0)


def test_immutability():
    """Test that configuration is immutable after creation."""
    config = ChunkingConfig()
    with pytest.raises(AttributeError):
        config.chunk_size = 200
    with pytest.raises(AttributeError):
        config.chunk_overlap = 20
    with pytest.raises(AttributeError):
        config.use_advanced_chunking = True
    with pytest.raises(AttributeError):
        config.min_chunk_size = 30
    with pytest.raises(AttributeError):
        config.max_chunk_size = 150


def test_config_string_representation():
    """Test that configuration has meaningful string representation."""
    config = ChunkingConfig(chunk_size=512, chunk_overlap=50, use_advanced_chunking=True, min_chunk_size=25, max_chunk_size=100, model_name='text-embedding-3-small')
    str_repr = str(config)
    assert '512' in str_repr
    assert '50' in str_repr
    assert 'True' in str_repr
    assert '25' in str_repr
    assert '100' in str_repr
    assert 'text-embedding-3-small' in str_repr