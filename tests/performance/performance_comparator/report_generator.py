"""Module for generating performance comparison reports."""

from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from loguru import logger

# Define report sections and templates
REPORT_HEADER = """# Weaviate Performance Comparison Report
Generated on: {timestamp}

## Test Parameters
- Document Count: {doc_count}
- Query Count: {query_count}
- Test Duration: {duration} seconds
"""

METRIC_TABLE_HEADER = """
| Metric | v3 | v4 | Difference | % Change |
|--------|----|----|------------|----------|"""

METRIC_ROW = """
| {metric} | {v3:.2f} | {v4:.2f} | {difference:+.2f} | {percent_change:+.2f}% |"""

SUMMARY_TEMPLATE = """
## Key Findings
{findings}

## Recommendations
{recommendations}
"""


def format_metric_table(metrics_df: pd.DataFrame) -> str:
    """Format metrics DataFrame as a markdown table.

    Args:
        metrics_df: DataFrame containing metric comparisons

    Returns:
        Formatted markdown table string
    """
    table = METRIC_TABLE_HEADER

    for _, row in metrics_df.iterrows():
        table += METRIC_ROW.format(
            metric=row["metric"],
            v3=row["v3"],
            v4=row["v4"],
            difference=row["difference"],
            percent_change=row["percent_change"],
        )

    return table


def generate_findings(metrics_df: pd.DataFrame) -> str:
    """Generate key findings from metrics comparison.

    Args:
        metrics_df: DataFrame containing metric comparisons

    Returns:
        Formatted string of key findings
    """
    findings = []

    for _, row in metrics_df.iterrows():
        if abs(row["percent_change"]) > 10:  # Significant change threshold
            change = "improved" if row["percent_change"] > 0 else "degraded"
            findings.append(f"- {row['metric']} {change} by {abs(row['percent_change']):.1f}%")

    return "\n".join(findings) if findings else "- No significant changes observed"


def generate_recommendations(metrics_df: pd.DataFrame) -> str:
    """Generate recommendations based on metrics comparison.

    Args:
        metrics_df: DataFrame containing metric comparisons

    Returns:
        Formatted string of recommendations
    """
    recommendations = []

    # Check for performance degradation
    degraded_metrics = metrics_df[metrics_df["percent_change"] < -10]
    if not degraded_metrics.empty:
        recommendations.append(
            "- Investigate performance degradation in: "
            + ", ".join(degraded_metrics["metric"].tolist())
        )

    # Check for failed operations
    failed_ops = metrics_df[(metrics_df["metric"].str.contains("Failed")) & (metrics_df["v4"] > 0)]
    if not failed_ops.empty:
        recommendations.append(
            "- Address failed operations in v4: " + ", ".join(failed_ops["metric"].tolist())
        )

    if not recommendations:
        recommendations.append("- No specific recommendations at this time")

    return "\n".join(recommendations)


def generate_report(
    metrics_df: pd.DataFrame, v3_results: Dict, v4_results: Dict, output_dir: str
) -> str:
    """Generate a complete performance comparison report.

    Args:
        metrics_df: DataFrame containing metric comparisons
        v3_results: Results from v3 tests
        v4_results: Results from v4 tests
        output_dir: Directory to save the report

    Returns:
        Path to the generated report file
    """
    try:
        # Extract test parameters
        doc_count = v3_results.get("test_parameters", {}).get("document_count", 0)
        query_count = v3_results.get("test_parameters", {}).get("query_count", 0)
        duration = v3_results.get("test_parameters", {}).get("duration_seconds", 0)

        # Generate report sections
        header = REPORT_HEADER.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            doc_count=doc_count,
            query_count=query_count,
            duration=duration,
        )

        metric_table = format_metric_table(metrics_df)
        findings = generate_findings(metrics_df)
        recommendations = generate_recommendations(metrics_df)

        summary = SUMMARY_TEMPLATE.format(findings=findings, recommendations=recommendations)

        # Combine all sections
        report_content = f"{header}\n{metric_table}\n{summary}"

        # Save report
        output_path = Path(output_dir) / f"performance_comparison_{datetime.now():%Y%m%d_%H%M%S}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

        logger.info(f"Report generated: {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise
