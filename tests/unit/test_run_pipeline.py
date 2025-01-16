"""Tests for run_pipeline.py script.

The project has two entry points:
1. run_pipeline.py - CLI script that handles argument parsing and pipeline execution
2. src/main.py - Core module that can be imported and used programmatically

This test file focuses on the CLI functionality in run_pipeline.py, specifically:
- Parsing of pipeline step names from command line arguments
- Handling of default and custom arguments
- Error handling and output formatting

The core functionality is tested separately in:
- tests/unit/main/test_error_handling.py
- tests/unit/main/test_execution.py
- tests/unit/main/test_parameters.py
- tests/unit/main/test_validation.py
"""

from unittest.mock import MagicMock, patch

import pytest
from run_pipeline import main, parse_steps

from src.pipeline import PipelineStep


def test_parse_steps():
    """Test parsing of pipeline step names."""
    # Empty string returns all steps
    assert parse_steps("") == set(PipelineStep)

    # Single step
    assert parse_steps("LOAD") == {PipelineStep.LOAD}

    # Multiple steps
    assert parse_steps("LOAD,EMBED,INDEX") == {
        PipelineStep.LOAD,
        PipelineStep.EMBED,
        PipelineStep.INDEX,
    }

    # Case insensitive
    assert parse_steps("load,EMBED,Index") == {
        PipelineStep.LOAD,
        PipelineStep.EMBED,
        PipelineStep.INDEX,
    }

    # Whitespace handling
    assert parse_steps(" LOAD , EMBED , INDEX ") == {
        PipelineStep.LOAD,
        PipelineStep.EMBED,
        PipelineStep.INDEX,
    }

    # Invalid steps are skipped with warning
    with patch("builtins.print") as mock_print:
        steps = parse_steps("LOAD,INVALID,INDEX")
        assert steps == {PipelineStep.LOAD, PipelineStep.INDEX}
        mock_print.assert_called_once_with("Warning: Invalid step 'INVALID', skipping")


@patch("run_pipeline.Pipeline")
@patch("argparse.ArgumentParser.parse_args")
def test_main_with_defaults(mock_args, mock_pipeline_cls):
    """Test main function with default arguments."""
    # Setup mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline_cls.return_value = mock_pipeline
    mock_pipeline.process_documents.return_value = ["doc1", "doc2"]

    # Setup mock args with only required argument
    args = MagicMock()
    args.export_dir = "test_dir"
    args.steps = ""
    args.index_url = "http://localhost:8080"
    args.log_dir = "logs"
    args.batch_size = 100
    args.cache_host = "localhost"
    args.cache_port = 6379
    args.cache_ttl = 86400
    args.no_pii = False
    args.no_dedup = False
    args.summary_max_length = 150
    args.summary_min_length = 50
    args.cluster_count = 5
    args.min_cluster_size = 3
    mock_args.return_value = args

    # Run main
    with patch("builtins.print") as mock_print:
        main()

    # Verify Pipeline initialization
    mock_pipeline_cls.assert_called_once_with(
        export_dir="test_dir",
        index_url="http://localhost:8080",
        log_dir="logs",
        batch_size=100,
        cache_host="localhost",
        cache_port=6379,
        cache_ttl=86400,
    )

    # Verify process_documents call
    mock_pipeline.process_documents.assert_called_once()
    call_kwargs = mock_pipeline.process_documents.call_args[1]
    assert call_kwargs["steps"] == set(PipelineStep)
    assert call_kwargs["detect_pii"] is True
    assert call_kwargs["deduplicate"] is True
    assert call_kwargs["summary_config"].max_length == 150
    assert call_kwargs["summary_config"].min_length == 50
    assert call_kwargs["cluster_config"].n_clusters == 5
    assert call_kwargs["cluster_config"].min_cluster_size == 3

    # Verify output
    mock_print.assert_any_call("\nProcessing complete. Processed 2 documents")
    mock_print.assert_any_call("Check logs/pipeline.json for detailed logs")


@patch("run_pipeline.Pipeline")
@patch("argparse.ArgumentParser.parse_args")
def test_main_with_custom_args(mock_args, mock_pipeline_cls):
    """Test main function with custom arguments."""
    # Setup mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline_cls.return_value = mock_pipeline
    mock_pipeline.process_documents.return_value = ["doc1"]

    # Setup mock args with custom values
    args = MagicMock()
    args.export_dir = "test_dir"
    args.steps = "LOAD,EMBED"
    args.index_url = "http://custom:8080"
    args.log_dir = "custom_logs"
    args.batch_size = 50
    args.cache_host = "custom_host"
    args.cache_port = 6380
    args.cache_ttl = 3600
    args.no_pii = True
    args.no_dedup = True
    args.summary_max_length = 200
    args.summary_min_length = 100
    args.cluster_count = 10
    args.min_cluster_size = 5
    mock_args.return_value = args

    # Run main
    with patch("builtins.print") as mock_print:
        main()

    # Verify Pipeline initialization
    mock_pipeline_cls.assert_called_once_with(
        export_dir="test_dir",
        index_url="http://custom:8080",
        log_dir="custom_logs",
        batch_size=50,
        cache_host="custom_host",
        cache_port=6380,
        cache_ttl=3600,
    )

    # Verify process_documents call
    mock_pipeline.process_documents.assert_called_once()
    call_kwargs = mock_pipeline.process_documents.call_args[1]
    assert call_kwargs["steps"] == {PipelineStep.LOAD, PipelineStep.EMBED}
    assert call_kwargs["detect_pii"] is False
    assert call_kwargs["deduplicate"] is False
    assert call_kwargs["summary_config"].max_length == 200
    assert call_kwargs["summary_config"].min_length == 100
    assert call_kwargs["cluster_config"].n_clusters == 10
    assert call_kwargs["cluster_config"].min_cluster_size == 5

    # Verify output
    mock_print.assert_any_call("\nProcessing complete. Processed 1 documents")
    mock_print.assert_any_call("Check custom_logs/pipeline.json for detailed logs")


@patch("run_pipeline.Pipeline")
@patch("argparse.ArgumentParser.parse_args")
def test_main_error_handling(mock_args, mock_pipeline_cls):
    """Test main function error handling."""
    # Setup mock pipeline to raise an error
    mock_pipeline = MagicMock()
    mock_pipeline_cls.return_value = mock_pipeline
    mock_pipeline.process_documents.side_effect = Exception("Test error")

    # Setup mock args
    args = MagicMock()
    args.export_dir = "test_dir"
    args.steps = ""
    args.index_url = "http://localhost:8080"
    args.log_dir = "logs"
    args.batch_size = 100
    args.cache_host = "localhost"
    args.cache_port = 6379
    args.cache_ttl = 86400
    args.no_pii = False
    args.no_dedup = False
    args.summary_max_length = 150
    args.summary_min_length = 50
    args.cluster_count = 5
    args.min_cluster_size = 3
    mock_args.return_value = args

    # Run main and verify it handles the error
    with patch("builtins.print") as mock_print, patch("sys.stderr", mock_print.return_value):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        mock_print.assert_called_once_with("Error: Test error", file=mock_print.return_value)
