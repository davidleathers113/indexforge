"""Tests for main module parameter handling.

This module focuses on testing parameter validation and defaults.
Other aspects are tested in:
- test_execution.py - Tests pipeline initialization and execution
- test_validation.py - Tests parameter validation rules
- test_run_pipeline.py - Tests CLI functionality
"""

from pathlib import Path

import pytest

from src.main import init_pipeline, run_pipeline
from src.pipeline.errors import ValidationError


def test_default_parameters(pipeline_with_mocks, tmp_path):
    """Test that default parameters are used when not provided."""
    export_dir = tmp_path / "test_dir"
    export_dir.mkdir()
    pipeline = run_pipeline(
        export_dir=str(export_dir), index_url="http://localhost:8080"
    )
    assert pipeline._export_dir == export_dir
    assert pipeline._index_url == "http://localhost:8080"
    assert pipeline._log_dir == Path("logs")
    assert pipeline._batch_size == 100
    assert pipeline._cache_host == "localhost"
    assert pipeline._cache_port == 6379
    assert pipeline._cache_ttl == 86400


def test_custom_parameters(pipeline_with_mocks, tmp_path):
    """Test that custom parameters override defaults."""
    export_dir = tmp_path / "test_dir"
    export_dir.mkdir()
    pipeline = run_pipeline(
        export_dir=str(export_dir),
        index_url="http://custom:8080",
        log_dir="custom_logs",
        batch_size=50,
        cache_host="custom_host",
        cache_port=6380,
        cache_ttl=3600,
    )
    assert pipeline._export_dir == export_dir
    assert pipeline._index_url == "http://custom:8080"
    assert pipeline._log_dir == Path("custom_logs")
    assert pipeline._batch_size == 50
    assert pipeline._cache_host == "custom_host"
    assert pipeline._cache_port == 6380
    assert pipeline._cache_ttl == 3600


def test_parameter_validation(pipeline_with_mocks, tmp_path):
    """Test that parameters are validated before pipeline initialization."""
    with pytest.raises(
        ValidationError, match="export_dir is required and must be a string"
    ):
        run_pipeline(export_dir="", index_url="http://localhost:8080")
    with pytest.raises(ValidationError, match="Invalid index URL format"):
        run_pipeline(export_dir=str(tmp_path), index_url="invalid-url")
    with pytest.raises(
        ValidationError, match="batch_size must be a positive integer"
    ):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            batch_size=0,
        )
    with pytest.raises(
        ValidationError, match="cache_port must be between 0 and 65535"
    ):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            cache_port=70000,
        )
    with pytest.raises(
        ValidationError, match="cache_ttl must be a positive integer"
    ):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            cache_ttl=-1,
        )


def test_parameter_types(pipeline_with_mocks, tmp_path):
    """Test parameter type validation."""
    with pytest.raises(ValidationError, match="batch_size must be int"):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            batch_size="not a number",
        )
    with pytest.raises(ValidationError, match="cache_port must be int"):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            cache_port="not a number",
        )
    with pytest.raises(ValidationError, match="cache_ttl must be int"):
        run_pipeline(
            export_dir=str(tmp_path),
            index_url="http://localhost:8080",
            cache_ttl="not a number",
        )


def test_argument_parsing(
    mock_argparse_parse_args, mock_cli_state, pipeline_with_mocks, tmp_path
):
    """Test CLI argument parsing."""
    export_dir = tmp_path / "test_dir"
    export_dir.mkdir()
    mock_cli_state.set_args(
        export_dir=str(export_dir),
        index_url="http://custom:8080",
        log_dir="custom_logs",
        batch_size=50,
        cache_host="custom_host",
        cache_port=6380,
        cache_ttl=3600,
    )
    pipeline = init_pipeline(export_dir=str(export_dir))
    assert pipeline._export_dir == export_dir
    assert pipeline._index_url == "http://custom:8080"
    assert pipeline._log_dir == Path("custom_logs")
    assert pipeline._batch_size == 50
    assert pipeline._cache_host == "custom_host"
    assert pipeline._cache_port == 6380
    assert pipeline._cache_ttl == 3600


def test_argument_parsing_error_handling(
    mock_argparse_parse_args, mock_cli_state, pipeline_with_mocks
):
    """Test handling of argument parsing errors."""
    mock_cli_state.error_mode = True
    with pytest.raises(
        ValueError, match="Argument parsing failed in error mode"
    ):
        init_pipeline(export_dir="test_dir")
    errors = mock_cli_state.get_errors()
    assert len(errors) > 0
    assert "Argument parsing failed in error mode" in str(errors[0])
