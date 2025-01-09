"""Tests for main module input validation rules.

This module focuses on testing the validation rules for input parameters.
Type coercion and parameter handling edge cases are tested in test_parameters.py.
"""
import pytest
from pathlib import Path
from src.main import run_pipeline
from src.pipeline.errors import ValidationError

def test_validate_url(pipeline_with_mocks, tmp_path):
    """Test URL validation rules."""
    export_dir = tmp_path / 'test_dir'
    export_dir.mkdir()
    valid_urls = ['http://localhost:8080', 'https://example.com', 'http://127.0.0.1:8080', 'https://api.example.com/v1', 'http://sub.domain.example.com:8080']
    for url in valid_urls:
        pipeline = run_pipeline(export_dir=str(export_dir), index_url=url)
        assert pipeline._index_url == url
    invalid_urls = ['invalid-url', 'http://', 'localhost', '', 'ftp://example.com', 'http://a b.com', 'http:/example.com', 'http:///example.com']
    for url in invalid_urls:
        with pytest.raises(ValidationError, match='Invalid index URL format'):
            run_pipeline(export_dir=str(export_dir), index_url=url)

def test_validate_required_parameters(pipeline_with_mocks, tmp_path):
    """Test validation of required parameters."""
    with pytest.raises(ValidationError, match='export_dir is required and must be a string'):
        run_pipeline(export_dir='', index_url='http://localhost:8080')
    with pytest.raises(ValidationError, match='export_dir is required and must be a string'):
        run_pipeline(export_dir=None, index_url='http://localhost:8080')

def test_validate_numeric_ranges(pipeline_with_mocks, tmp_path):
    """Test validation of numeric parameter ranges."""
    export_dir = tmp_path / 'test_dir'
    export_dir.mkdir()
    with pytest.raises(ValidationError, match='batch_size must be a positive integer'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', batch_size=0)
    with pytest.raises(ValidationError, match='batch_size must be a positive integer'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', batch_size=-1)
    with pytest.raises(ValidationError, match='cache_port must be between 0 and 65535'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', cache_port=-1)
    with pytest.raises(ValidationError, match='cache_port must be between 0 and 65535'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', cache_port=65536)
    with pytest.raises(ValidationError, match='cache_ttl must be a positive integer'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', cache_ttl=0)
    with pytest.raises(ValidationError, match='cache_ttl must be a positive integer'):
        run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', cache_ttl=-1)

def test_validate_url_parameter(pipeline_with_mocks, tmp_path):
    """Test validation of URL parameter."""
    export_dir = tmp_path / 'test_dir'
    export_dir.mkdir()
    invalid_urls = ['invalid-url', 'http://', 'localhost:8080', '', 'ftp://example.com', 'http://a b.com', 'http:/example.com', 'http:///example.com']
    for url in invalid_urls:
        with pytest.raises(ValidationError, match='Invalid index URL format'):
            run_pipeline(export_dir=str(export_dir), index_url=url)

def test_validate_valid_parameters(pipeline_with_mocks, tmp_path):
    """Test that valid parameters pass validation."""
    valid_params = [{'export_dir': str(tmp_path / 'test1'), 'index_url': 'http://localhost:8080', 'log_dir': 'logs', 'batch_size': 100, 'cache_host': 'localhost', 'cache_port': 6379, 'cache_ttl': 86400}, {'export_dir': str(tmp_path / 'test2'), 'index_url': 'https://example.com', 'log_dir': str(tmp_path / 'logs'), 'batch_size': 1, 'cache_host': 'redis', 'cache_port': 0, 'cache_ttl': 1}, {'export_dir': str(tmp_path / 'test3'), 'index_url': 'http://127.0.0.1:8080', 'log_dir': str(tmp_path / 'logs2'), 'batch_size': 1000000, 'cache_host': '127.0.0.1', 'cache_port': 65535, 'cache_ttl': 31536000}]
    for params in valid_params:
        Path(params['export_dir']).mkdir(parents=True)
        pipeline = run_pipeline(**params)
        assert pipeline._export_dir == Path(params['export_dir'])
        assert pipeline._index_url == params['index_url']
        assert pipeline._log_dir == Path(params['log_dir'])
        assert pipeline._batch_size == params['batch_size']
        assert pipeline._cache_host == params['cache_host']
        assert pipeline._cache_port == params['cache_port']
        assert pipeline._cache_ttl == params['cache_ttl']

def test_export_dir_required(pipeline_with_mocks, tmp_path):
    """Test that export_dir is required."""
    with pytest.raises(ValidationError, match='export_dir is required and must be a string'):
        run_pipeline(index_url='http://localhost:8080')
    with pytest.raises(ValidationError, match='export_dir is required and must be a string'):
        run_pipeline(export_dir=None, index_url='http://localhost:8080')
    with pytest.raises(ValidationError, match='export_dir is required and must be a string'):
        run_pipeline(export_dir='', index_url='http://localhost:8080')

def test_index_url_validation(pipeline_with_mocks, tmp_path):
    """Test index URL validation rules."""
    export_dir = tmp_path / 'test_dir'
    export_dir.mkdir()
    with pytest.raises(ValidationError, match='Invalid index URL format'):
        run_pipeline(export_dir=str(export_dir), index_url='not-a-url')
    with pytest.raises(ValidationError, match='Invalid index URL format'):
        run_pipeline(export_dir=str(export_dir), index_url='ftp://example.com')
    with pytest.raises(ValidationError, match='Invalid index URL format'):
        run_pipeline(export_dir=str(export_dir), index_url='http://')
    pipeline = run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080')
    assert pipeline._index_url == 'http://localhost:8080'