"""Tests for summarizer configuration."""
from src.utils.summarizer import SummarizerConfig

def test_summarizer_config_defaults():
    """Test SummarizerConfig default values."""
    config = SummarizerConfig()
    assert config.max_length == 150
    assert config.min_length == 50
    assert config.do_sample is False
    assert config.temperature == 0.7
    assert config.top_p == 0.9
    assert config.chunk_size == 1024
    assert config.chunk_overlap == 100

def test_summarizer_config_custom_values():
    """Test SummarizerConfig with custom values."""
    config = SummarizerConfig(max_length=200, min_length=100, do_sample=True, temperature=0.8, top_p=0.95, chunk_size=512, chunk_overlap=50)
    assert config.max_length == 200
    assert config.min_length == 100
    assert config.do_sample is True
    assert config.temperature == 0.8
    assert config.top_p == 0.95
    assert config.chunk_size == 512
    assert config.chunk_overlap == 50