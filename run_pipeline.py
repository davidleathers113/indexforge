"""Script to run the Notion export processing pipeline.

This script provides a command-line interface for running the document processing
pipeline on Notion exports. It supports configurable pipeline steps, caching,
summarization, and clustering options through command-line arguments.

Functions:
    parse_args: Parse command line arguments
    parse_steps: Convert step names to PipelineStep enums
    main: Main entry point for the pipeline

Example:
    ```bash
    # Run all pipeline steps
    python run_pipeline.py path/to/notion/export

    # Run specific steps with custom settings
    python run_pipeline.py path/to/notion/export \\
        --steps LOAD,SUMMARIZE,INDEX \\
        --summary-max-length 200 \\
        --no-pii
    ```
"""

import argparse
import sys

from src.models.settings import ClusteringConfig, SummarizerConfig
from src.pipeline import Pipeline, PipelineStep


def parse_args() -> argparse.Namespace:
    """Parse and validate command line arguments for the pipeline.

    This function sets up the argument parser with all available pipeline
    configuration options, including pipeline steps, service connections,
    and processing parameters.

    Returns:
        argparse.Namespace: Parsed command line arguments with the following fields:
            - export_dir (str): Path to Notion export directory
            - steps (str, optional): Comma-separated list of steps to run
            - index_url (str): Weaviate URL, defaults to "http://localhost:8080"
            - log_dir (str): Directory for logs, defaults to "logs"
            - batch_size (int): Batch size, defaults to 100
            - cache_host (str): Redis cache host, defaults to "localhost"
            - cache_port (int): Redis cache port, defaults to 6379
            - cache_ttl (int): Cache TTL in seconds, defaults to 86400
            - no_pii (bool): Whether to skip PII detection
            - no_dedup (bool): Whether to skip deduplication
            - summary_max_length (int): Maximum summary length, defaults to 150
            - summary_min_length (int): Minimum summary length, defaults to 50
            - cluster_count (int): Number of clusters, defaults to 5
            - min_cluster_size (int): Minimum cluster size, defaults to 3

    Example:
        ```python
        args = parse_args()
        print(f"Processing documents from {args.export_dir}")
        if not args.no_pii:
            print("PII detection enabled")
        ```
    """
    parser = argparse.ArgumentParser(description="Run the document processing pipeline")

    # Required arguments
    parser.add_argument("export_dir", help="Path to Notion export directory")

    # Optional arguments
    parser.add_argument("--steps", help="Comma-separated list of steps to run (default: all)")
    parser.add_argument("--index-url", default="http://localhost:8080", help="Weaviate URL")
    parser.add_argument("--log-dir", default="logs", help="Directory for logs")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--cache-host", default="localhost", help="Redis cache host")
    parser.add_argument("--cache-port", type=int, default=6379, help="Redis cache port")
    parser.add_argument("--cache-ttl", type=int, default=86400, help="Cache TTL in seconds")
    parser.add_argument("--no-pii", action="store_true", help="Skip PII detection")
    parser.add_argument("--no-dedup", action="store_true", help="Skip deduplication")

    # Summarization config
    parser.add_argument("--summary-max-length", type=int, default=150)
    parser.add_argument("--summary-min-length", type=int, default=50)

    # Clustering config
    parser.add_argument("--cluster-count", type=int, default=5)
    parser.add_argument("--min-cluster-size", type=int, default=3)

    return parser.parse_args()


def parse_steps(steps_str: str) -> set[PipelineStep]:
    """Parse pipeline steps from a comma-separated string.

    Converts a comma-separated string of step names into a set of PipelineStep
    enum values. Invalid step names are ignored with a warning message.

    Args:
        steps_str (str): Comma-separated string of step names (case-insensitive)

    Returns:
        Set[PipelineStep]: Set of PipelineStep enum values. If steps_str is empty
            or None, returns all available pipeline steps.

    Example:
        ```python
        # Get specific steps
        steps = parse_steps("LOAD,SUMMARIZE,INDEX")

        # Get all steps
        all_steps = parse_steps("")
        ```
    """
    if not steps_str:
        return set(PipelineStep)

    steps = set()
    step_names = steps_str.upper().split(",")
    for name in step_names:
        try:
            steps.add(PipelineStep[name.strip()])
        except KeyError:
            print(f"Warning: Invalid step '{name}', skipping")
    return steps


def main():
    """Main entry point for the pipeline script.

    This function orchestrates the pipeline execution by:
    1. Parsing command line arguments
    2. Initializing the pipeline with the specified configuration
    3. Running the pipeline with the requested steps
    4. Handling any errors that occur during execution

    Returns:
        int: 0 for successful execution, 1 for errors

    Raises:
        SystemExit: With exit code 1 if an unhandled error occurs

    Example:
        ```python
        if __name__ == "__main__":
            sys.exit(main())
        ```
    """
    try:
        args = parse_args()
        pipeline = Pipeline(
            export_dir=args.export_dir,
            index_url=args.index_url,
            log_dir=args.log_dir,
            batch_size=args.batch_size,
            cache_host=args.cache_host,
            cache_port=args.cache_port,
            cache_ttl=args.cache_ttl,
        )

        steps = parse_steps(args.steps)
        docs = pipeline.process_documents(
            steps=steps,
            detect_pii=not args.no_pii,
            deduplicate=not args.no_dedup,
            summary_config=SummarizerConfig(
                max_length=args.summary_max_length, min_length=args.summary_min_length
            ),
            cluster_config=ClusteringConfig(
                n_clusters=args.cluster_count, min_cluster_size=args.min_cluster_size
            ),
        )

        print(f"\nProcessing complete. Processed {len(docs)} documents")
        print(f"Check {args.log_dir}/pipeline.json for detailed logs")
        return 0
    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())
