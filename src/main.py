"""Main entry point for the pipeline.

This module serves as the primary entry point for the document processing pipeline.
It provides both command-line and programmatic interfaces for pipeline execution.

Key Features:
1. Pipeline Configuration:
   - Parameter validation and normalization
   - Environment variable support
   - Command line argument parsing
   - Default value handling

2. Pipeline Execution:
   - Resource management
   - Error handling
   - Progress tracking
   - Cleanup on completion

3. Interface Options:
   - Command line execution
   - Programmatic API
   - Testing interface
   - Configuration flexibility

Usage:
    Command Line:
    ```bash
    python main.py /path/to/export --index-url http://localhost:8080
    ```

    Programmatic:
    ```python
    from src.main import run_pipeline

    pipeline = run_pipeline(
        export_dir="/path/to/export",
        index_url="http://localhost:8080",
        batch_size=100
    )
    ```

Configuration:
    - export_dir: Directory containing documents to process
    - index_url: Vector index service endpoint
    - log_dir: Directory for log files
    - batch_size: Number of documents per batch
    - cache_host: Redis cache host
    - cache_port: Redis cache port
    - cache_ttl: Cache time-to-live in seconds

Environment Variables:
    - PIPELINE_INDEX_URL: Vector index service URL
    - PIPELINE_LOG_DIR: Log directory path
    - PIPELINE_BATCH_SIZE: Processing batch size
    - PIPELINE_CACHE_HOST: Cache host
    - PIPELINE_CACHE_PORT: Cache port
    - PIPELINE_CACHE_TTL: Cache TTL

Error Handling:
    - ValidationError: Configuration validation failures
    - PipelineError: Processing and execution errors
    - ResourceError: Resource management issues
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Union

from pipeline.context import managed_pipeline
from pipeline.core import Pipeline
from pipeline.errors import PipelineError, ValidationError
from pipeline.parameters import get_env_value, normalize_parameters, validate_parameters


def run_pipeline(
    export_dir: Optional[Union[str, Path]] = None,
    index_url: Optional[str] = None,
    log_dir: Union[str, Path] = "logs",
    batch_size: Union[int, str] = 100,
    cache_host: Optional[str] = None,
    cache_port: Optional[int] = None,
    cache_ttl: Optional[int] = None,
) -> Pipeline:
    """Run pipeline with direct parameter input (for testing and programmatic use).

    This function provides a programmatic interface to run the pipeline with
    flexible parameter configuration. It handles parameter normalization,
    validation, and pipeline initialization.

    Args:
        export_dir: Directory containing documents to process
        index_url: Vector index service endpoint
        log_dir: Directory for log files
        batch_size: Number of documents per batch
        cache_host: Redis cache host
        cache_port: Redis cache port
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Initialized Pipeline instance

    Raises:
        ValidationError: If parameters fail validation
        PipelineError: If pipeline initialization fails
    """
    # Normalize and validate parameters
    params = normalize_parameters(
        export_dir=export_dir,
        index_url=index_url,
        log_dir=log_dir,
        batch_size=batch_size,
        cache_host=cache_host,
        cache_port=cache_port,
        cache_ttl=cache_ttl,
    )
    validate_parameters(**params)

    return Pipeline(**params)


def main(
    export_dir: Union[str, Path],
    index_url: Optional[str] = None,
    log_dir: Union[str, Path] = "logs",
    batch_size: Union[int, str] = 100,
    cache_host: Optional[str] = None,
    cache_port: Optional[int] = None,
    cache_ttl: Optional[int] = None,
) -> Pipeline:
    """Initialize and run the pipeline (backward compatibility).

    This function maintains backward compatibility with existing code that
    uses the main() entry point. It delegates to run_pipeline() for actual
    execution.

    Args:
        export_dir: Directory containing documents to process
        index_url: Vector index service endpoint
        log_dir: Directory for log files
        batch_size: Number of documents per batch
        cache_host: Redis cache host
        cache_port: Redis cache port
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Initialized Pipeline instance

    Raises:
        ValidationError: If parameters fail validation
        PipelineError: If pipeline initialization fails
    """
    return run_pipeline(
        export_dir=export_dir,
        index_url=index_url,
        log_dir=log_dir,
        batch_size=batch_size,
        cache_host=cache_host,
        cache_port=cache_port,
        cache_ttl=cache_ttl,
    )


def init_pipeline(
    export_dir: Union[str, Path],
    index_url: Optional[str] = None,
    log_dir: Union[str, Path] = "logs",
    batch_size: Union[int, str] = 100,
    cache_host: Optional[str] = None,
    cache_port: Optional[int] = None,
    cache_ttl: Optional[int] = None,
) -> Pipeline:
    """Initialize pipeline with validated parameters.

    This function provides a complete pipeline initialization with both
    command line and environment variable support. It handles parameter
    parsing, validation, and pipeline setup.

    Args:
        export_dir: Directory containing documents to process
        index_url: Vector index service endpoint
        log_dir: Directory for log files
        batch_size: Number of documents per batch
        cache_host: Redis cache host
        cache_port: Redis cache port
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Initialized Pipeline instance

    Raises:
        ValidationError: If parameters fail validation
        PipelineError: If pipeline initialization fails
    """
    # Set up parser for documentation/help text
    parser = argparse.ArgumentParser()
    parser.add_argument("export_dir", help="Directory containing Notion export")
    parser.add_argument("--index-url", help="URL of vector index service")
    parser.add_argument("--log-dir", help="Directory for log files")
    parser.add_argument("--batch-size", type=int, help="Batch size for processing")
    parser.add_argument("--cache-host", help="Cache host")
    parser.add_argument("--cache-port", type=int, help="Cache port")
    parser.add_argument("--cache-ttl", type=int, help="Cache TTL")

    # Create initial namespace with provided parameters
    from argparse import Namespace

    initial_args = Namespace(
        export_dir=export_dir,
        index_url=index_url,
        log_dir=log_dir,
        batch_size=batch_size,
        cache_host=cache_host,
        cache_port=cache_port,
        cache_ttl=cache_ttl,
    )

    # Parse arguments, using initial args as defaults
    args = parser.parse_args([], namespace=initial_args)

    # Get environment variables for any unset values
    args.index_url = get_env_value("INDEX_URL", args.index_url or "http://localhost:8080")
    args.log_dir = get_env_value("LOG_DIR", args.log_dir)
    args.batch_size = get_env_value("BATCH_SIZE", args.batch_size)
    args.cache_host = get_env_value("CACHE_HOST", args.cache_host or "localhost")
    args.cache_port = get_env_value("CACHE_PORT", args.cache_port or 6379)
    args.cache_ttl = get_env_value("CACHE_TTL", args.cache_ttl or 86400)

    return run_pipeline(
        export_dir=args.export_dir,
        index_url=args.index_url,
        log_dir=args.log_dir,
        batch_size=args.batch_size,
        cache_host=args.cache_host,
        cache_port=args.cache_port,
        cache_ttl=args.cache_ttl,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Notion export and build search index")
    parser.add_argument("export_dir", help="Directory containing Notion export")
    parser.add_argument(
        "--index-url",
        default=None,  # Use environment/default in main()
        help="URL of vector index service",
    )
    parser.add_argument("--log-dir", default="logs", help="Directory for log files")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")

    try:
        args = parser.parse_args()
        pipeline = init_pipeline(
            export_dir=args.export_dir,
            index_url=args.index_url,
            log_dir=args.log_dir,
            batch_size=args.batch_size,
        )

        with managed_pipeline(pipeline) as p:
            p.process_documents()

    except ValidationError as e:
        print(f"Configuration error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except PipelineError as e:
        if e.cause:
            print(f"Pipeline error: {str(e)} caused by {str(e.cause)}", file=sys.stderr)
        else:
            print(f"Pipeline error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)
