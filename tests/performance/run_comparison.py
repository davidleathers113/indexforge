"""Script to run and compare performance tests between Weaviate v3 and v4."""

from datetime import datetime
import json
import os
from typing import Dict

from loguru import logger
import pandas as pd


def load_results(filename: str) -> Dict:
    """Load test results from file.

    Args:
        filename: Results file path

    Returns:
        Test results dictionary
    """
    with open(filename) as f:
        return json.load(f)


def compare_metrics(v3_results: Dict, v4_results: Dict) -> pd.DataFrame:
    """Compare metrics between v3 and v4 results.

    Args:
        v3_results: Results from v3 tests
        v4_results: Results from v4 tests

    Returns:
        DataFrame with metric comparisons
    """
    metrics = []

    # Compare import metrics
    v3_import = v3_results["import_metrics"]
    v4_import = v4_results["import_metrics"]

    metrics.extend(
        [
            {
                "metric": "Import Duration (s)",
                "v3": v3_import["duration_seconds"],
                "v4": v4_import["duration_seconds"],
                "difference": v4_import["duration_seconds"] - v3_import["duration_seconds"],
                "percent_change": (
                    (v4_import["duration_seconds"] - v3_import["duration_seconds"])
                    / v3_import["duration_seconds"]
                )
                * 100,
            },
            {
                "metric": "Documents/Second",
                "v3": v3_import["docs_per_second"],
                "v4": v4_import["docs_per_second"],
                "difference": v4_import["docs_per_second"] - v3_import["docs_per_second"],
                "percent_change": (
                    (v4_import["docs_per_second"] - v3_import["docs_per_second"])
                    / v3_import["docs_per_second"]
                )
                * 100,
            },
            {
                "metric": "Failed Imports",
                "v3": v3_import["failed_imports"],
                "v4": v4_import["failed_imports"],
                "difference": v4_import["failed_imports"] - v3_import["failed_imports"],
                "percent_change": (
                    (v4_import["failed_imports"] - v3_import["failed_imports"])
                    / max(v3_import["failed_imports"], 1)
                )
                * 100,
            },
        ]
    )

    # Compare search metrics
    v3_search = v3_results["search_metrics"]
    v4_search = v4_results["search_metrics"]

    metrics.extend(
        [
            {
                "metric": "Search Duration (s)",
                "v3": v3_search["duration_seconds"],
                "v4": v4_search["duration_seconds"],
                "difference": v4_search["duration_seconds"] - v3_search["duration_seconds"],
                "percent_change": (
                    (v4_search["duration_seconds"] - v3_search["duration_seconds"])
                    / v3_search["duration_seconds"]
                )
                * 100,
            },
            {
                "metric": "Queries/Second",
                "v3": v3_search["queries_per_second"],
                "v4": v4_search["queries_per_second"],
                "difference": v4_search["queries_per_second"] - v3_search["queries_per_second"],
                "percent_change": (
                    (v4_search["queries_per_second"] - v3_search["queries_per_second"])
                    / v3_search["queries_per_second"]
                )
                * 100,
            },
            {
                "metric": "Avg Query Time (s)",
                "v3": v3_search["avg_query_time"],
                "v4": v4_search["avg_query_time"],
                "difference": v4_search["avg_query_time"] - v3_search["avg_query_time"],
                "percent_change": (
                    (v4_search["avg_query_time"] - v3_search["avg_query_time"])
                    / v3_search["avg_query_time"]
                )
                * 100,
            },
            {
                "metric": "Failed Queries",
                "v3": v3_search["failed_queries"],
                "v4": v4_search["failed_queries"],
                "difference": v4_search["failed_queries"] - v3_search["failed_queries"],
                "percent_change": (
                    (v4_search["failed_queries"] - v3_search["failed_queries"])
                    / max(v3_search["failed_queries"], 1)
                )
                * 100,
            },
        ]
    )

    return pd.DataFrame(metrics)


def generate_report(
    comparison_df: pd.DataFrame, v3_results: Dict, v4_results: Dict, output_file: str
):
    """Generate performance comparison report."""
    with open(output_file, "w") as f:
        f.write("# Weaviate Performance Comparison Report\n\n")

        # Test parameters
        f.write("## Test Parameters\n\n")
        f.write(f"- Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- V3 Version: {v3_results['weaviate_version']}\n")
        f.write(f"- V4 Version: {v4_results['weaviate_version']}\n")
        f.write(f"- Documents Tested: {v3_results['test_parameters']['num_documents']}\n")
        f.write(f"- Queries Tested: {v3_results['test_parameters']['num_queries']}\n")
        f.write(f"- Batch Size: {v3_results['test_parameters']['batch_size']}\n\n")

        # Metric comparison table
        f.write("## Performance Metrics\n\n")
        comparison_table = comparison_df.to_markdown(index=False, floatfmt=".2f")
        f.write(f"{comparison_table}\n\n")

        # Key findings
        f.write("## Key Findings\n\n")

        # Import performance
        import_speedup = -comparison_df[comparison_df["metric"] == "Import Duration (s)"][
            "percent_change"
        ].values[0]
        f.write("### Import Performance\n")
        if import_speedup > 0:
            f.write(f"- Import performance improved by {import_speedup:.1f}%\n")
        else:
            f.write(f"- Import performance decreased by {-import_speedup:.1f}%\n")

        docs_per_second_change = comparison_df[comparison_df["metric"] == "Documents/Second"][
            "percent_change"
        ].values[0]
        f.write(f"- Documents processed per second changed by {docs_per_second_change:+.1f}%\n\n")

        # Search performance
        search_speedup = -comparison_df[comparison_df["metric"] == "Search Duration (s)"][
            "percent_change"
        ].values[0]
        f.write("### Search Performance\n")
        if search_speedup > 0:
            f.write(f"- Search performance improved by {search_speedup:.1f}%\n")
        else:
            f.write(f"- Search performance decreased by {-search_speedup:.1f}%\n")

        queries_per_second_change = comparison_df[comparison_df["metric"] == "Queries/Second"][
            "percent_change"
        ].values[0]
        f.write(f"- Queries processed per second changed by {queries_per_second_change:+.1f}%\n\n")

        # Reliability
        failed_imports_v3 = v3_results["import_metrics"]["failed_imports"]
        failed_imports_v4 = v4_results["import_metrics"]["failed_imports"]
        failed_queries_v3 = v3_results["search_metrics"]["failed_queries"]
        failed_queries_v4 = v4_results["search_metrics"]["failed_queries"]

        f.write("### Reliability\n")
        f.write(f"- Failed imports: {failed_imports_v3} (v3) vs {failed_imports_v4} (v4)\n")
        f.write(f"- Failed queries: {failed_queries_v3} (v3) vs {failed_queries_v4} (v4)\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if import_speedup < -10:
            f.write("- Investigate import performance regression\n")
        if search_speedup < -10:
            f.write("- Investigate search performance regression\n")
        if failed_imports_v4 > failed_imports_v3:
            f.write("- Investigate increase in import failures\n")
        if failed_queries_v4 > failed_queries_v3:
            f.write("- Investigate increase in query failures\n")

        logger.info(f"Generated performance comparison report: {output_file}")


def main():
    """Run performance comparison between Weaviate v3 and v4."""
    # Load test results
    results_dir = "tests/performance"
    v3_results = None
    v4_results = None

    # Find most recent results for each version
    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            results = load_results(os.path.join(results_dir, filename))
            version = results["weaviate_version"]

            if version.startswith("3."):
                if v3_results is None or results["timestamp"] > v3_results["timestamp"]:
                    v3_results = results
            elif version.startswith("4."):
                if v4_results is None or results["timestamp"] > v4_results["timestamp"]:
                    v4_results = results

    if v3_results is None or v4_results is None:
        logger.error("Missing test results for one or both versions")
        return

    # Compare metrics
    comparison_df = compare_metrics(v3_results, v4_results)

    # Generate report
    report_file = os.path.join(
        results_dir, f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    generate_report(comparison_df, v3_results, v4_results, report_file)


if __name__ == "__main__":
    main()
