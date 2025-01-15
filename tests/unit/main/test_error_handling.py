"""Tests for main module error handling.

This module focuses on testing error handling and error propagation.
Other aspects are tested in:
- test_execution.py - Tests pipeline initialization and execution
- test_validation.py - Tests parameter validation rules
- test_parameters.py - Tests parameter handling
"""

from unittest.mock import MagicMock, patch

import pytest

from src.main import run_pipeline
from src.pipeline.errors import ValidationError


def test_error_propagation(tmp_path):
    """Test that errors are properly propagated."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with patch("src.main.Pipeline") as mock_pipeline:
        mock_instance = MagicMock()
        mock_pipeline.return_value = mock_instance
        mock_instance.process_documents.side_effect = ValueError(
            "Invalid value"
        )
        with pytest.raises(ValueError, match="Invalid value"):
            pipeline = run_pipeline(
                export_dir=str(test_dir), index_url="http://localhost:8080"
            )
            pipeline.process_documents()
        mock_instance.process_documents.side_effect = RuntimeError(
            "Runtime error"
        )
        with pytest.raises(RuntimeError, match="Runtime error"):
            pipeline = run_pipeline(
                export_dir=str(test_dir), index_url="http://localhost:8080"
            )
            pipeline.process_documents()
        mock_instance.process_documents.side_effect = Exception(
            "Generic error"
        )
        with pytest.raises(Exception, match="Generic error"):
            pipeline = run_pipeline(
                export_dir=str(test_dir), index_url="http://localhost:8080"
            )
            pipeline.process_documents()


def test_validation_error_handling(tmp_path):
    """Test that validation errors are properly handled."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with patch("src.main.Pipeline") as mock_pipeline:
        with pytest.raises(
            ValidationError,
            match="export_dir is required and must be a string",
        ):
            run_pipeline(export_dir="", index_url="http://localhost:8080")
        with pytest.raises(ValidationError, match="Invalid index URL format"):
            run_pipeline(export_dir=str(test_dir), index_url="invalid-url")
        with pytest.raises(
            ValidationError, match="batch_size must be a positive integer"
        ):
            run_pipeline(
                export_dir=str(test_dir),
                index_url="http://localhost:8080",
                batch_size=0,
            )
        mock_pipeline.assert_not_called()


def test_pipeline_error_handling(tmp_path):
    """Test that pipeline errors are properly handled."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with patch("src.main.Pipeline") as mock_pipeline:
        mock_pipeline.side_effect = RuntimeError(
            "Pipeline initialization failed"
        )
        with pytest.raises(
            RuntimeError, match="Pipeline initialization failed"
        ):
            run_pipeline(
                export_dir=str(test_dir), index_url="http://localhost:8080"
            )


def test_error_cleanup(tmp_path):
    """Test that resources are cleaned up after errors."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with patch("src.main.Pipeline") as mock_pipeline:
        mock_instance = MagicMock()
        mock_pipeline.return_value = mock_instance
        mock_instance.process_documents.side_effect = ValueError("Test error")
        pipeline = run_pipeline(
            export_dir=str(test_dir), index_url="http://localhost:8080"
        )
        with (
            pytest.raises(ValueError),
            patch("src.pipeline.context.managed_pipeline") as mock_context,
        ):
            cm = MagicMock()
            cm.__enter__.return_value = pipeline
            cm.__exit__.side_effect = lambda exc_type, exc_val, exc_tb: (
                mock_instance.cleanup(),
                False,
            )[-1]
            mock_context.return_value = cm
            with mock_context(pipeline):
                pipeline.process_documents()
        mock_instance.cleanup.assert_called_once()
