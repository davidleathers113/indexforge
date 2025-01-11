"""Main entry point for performance comparison."""

import argparse
from typing import Dict, Optional

from loguru import logger

from tests.performance.performance_comparator.data_loader import find_latest_results, load_results
from tests.performance.performance_comparator.metrics_comparator import compare_metrics
from tests.performance.performance_comparator.report_generator import generate_report


def setup_logging(log_file: Optional[str] = None) -> None:
    """Set up logging configuration.

    Args:
        log_file: Optional path to log file
    """
    logger.remove()  # Remove default handler

    # Add console handler
    logger.add(
        sink=lambda msg: print(msg),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <white>{message}</white>",
        level="INFO",
    )

    # Add file handler if specified
    if log_file:
        logger.add(sink=log_file, rotation="1 day", retention="7 days", level="DEBUG")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Compare performance between Weaviate versions")

    parser.add_argument(
        "--results-dir",
        type=str,
        default="tests/performance/results",
        help="Directory containing test results",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/performance/reports",
        help="Directory to save the comparison report",
    )

    parser.add_argument("--log-file", type=str, help="Path to log file (optional)")

    parser.add_argument("--v3-results", type=str, help="Specific v3 results file (optional)")

    parser.add_argument("--v4-results", type=str, help="Specific v4 results file (optional)")

    return parser.parse_args()


def load_version_results(
    results_dir: str, version: str, specific_file: Optional[str] = None
) -> Dict:
    """Load results for a specific version.

    Args:
        results_dir: Directory containing test results
        version: Version prefix to search for
        specific_file: Optional path to specific results file

    Returns:
        Dictionary containing test results
    """
    if specific_file:
        logger.info(f"Loading {version} results from {specific_file}")
        return load_results(specific_file)

    logger.info(f"Finding latest {version} results in {results_dir}")
    results = find_latest_results(results_dir, version)
    if not results:
        raise ValueError(f"No {version} results found in {results_dir}")

    return results


def main() -> None:
    """Main entry point for performance comparison."""
    args = parse_args()
    setup_logging(args.log_file)

    try:
        # Load test results
        v3_results = load_version_results(args.results_dir, "v3", args.v3_results)
        v4_results = load_version_results(args.results_dir, "v4", args.v4_results)

        # Compare metrics
        logger.info("Comparing metrics between versions")
        metrics_df = compare_metrics(v3_results, v4_results)

        # Generate report
        logger.info("Generating comparison report")
        report_path = generate_report(metrics_df, v3_results, v4_results, args.output_dir)

        logger.info(f"Performance comparison completed. Report saved to: {report_path}")

    except Exception as e:
        logger.error(f"Error during performance comparison: {e}")
        raise


if __name__ == "__main__":
    main()
