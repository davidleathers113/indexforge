"""Test core metrics tracking functionality."""

import pytest

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker


@pytest.fixture
def performance_tracker():
    """Setup BatchPerformanceTracker instance."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=100, window_size=5)


def test_metrics_history_management(performance_tracker):
    """
    Test metrics history management.

    Given: A BatchPerformanceTracker with window_size=5
    When: Recording more metrics than window size
    Then: History maintains correct window size and order
    """
    # Record more metrics than window size
    for i in range(7):
        performance_tracker.start_batch(50)
        performance_tracker.end_batch(45, 5, 100.0)

    assert len(performance_tracker.metrics_history) == 5  # Window size
    # Verify metrics are stored in chronological order
    timestamps = [m.timestamp for m in performance_tracker.metrics_history]
    assert timestamps == sorted(timestamps)


def test_metrics_aggregation(performance_tracker):
    """
    Test metrics aggregation over time.

    Given: A BatchPerformanceTracker with multiple recorded metrics
    When: Getting performance summary
    Then: Aggregated metrics are calculated correctly
    """
    # Record varied performance data
    test_data = [
        (40, 10, 100.0),  # 80% success
        (30, 20, 150.0),  # 60% success
        (50, 0, 200.0),  # 100% success
    ]

    for successful, failed, memory in test_data:
        performance_tracker.start_batch(successful + failed)
        performance_tracker.end_batch(successful, failed, memory)

    metrics = performance_tracker.get_performance_metrics()
    total_objects = sum(s + f for s, f, _ in test_data)
    total_successful = sum(s for s, _, _ in test_data)

    assert metrics["success_rate"] == total_successful / total_objects
    assert metrics["memory_usage_mb"] == 200.0  # Latest value


def test_time_series_tracking(performance_tracker):
    """
    Test time series metrics tracking.

    Given: A BatchPerformanceTracker recording metrics over time
    When: Analyzing metrics history
    Then: Time series data is maintained correctly
    """
    batch_sizes = [20, 30, 40]

    for size in batch_sizes:
        performance_tracker.start_batch(size)
        performance_tracker.end_batch(size - 2, 2, 100.0)

    history = performance_tracker.metrics_history
    assert len(history) == len(batch_sizes)

    # Verify chronological order and data integrity
    for i, metric in enumerate(history):
        assert metric.batch_size == batch_sizes[i]
        assert metric.successful_objects == batch_sizes[i] - 2
        assert metric.failed_objects == 2


def test_window_based_analysis(performance_tracker):
    """
    Test window-based metrics analysis.

    Given: A BatchPerformanceTracker with sliding window
    When: Recording metrics beyond window size
    Then: Analysis uses correct window of data
    """
    window_size = 5
    total_batches = window_size + 3

    # Record more batches than window size
    for i in range(total_batches):
        performance_tracker.start_batch(50)
        # Alternate between high and low success rates
        if i % 2 == 0:
            performance_tracker.end_batch(45, 5, 100.0)
        else:
            performance_tracker.end_batch(25, 25, 100.0)

    # Verify only window_size most recent metrics are used
    assert len(performance_tracker.metrics_history) == window_size

    # Verify metrics are from most recent batches
    success_rates = [
        m.successful_objects / (m.successful_objects + m.failed_objects)
        for m in performance_tracker.metrics_history
    ]
    # Last window_size success rates should alternate
    expected_pattern = [0.9 if i % 2 == 0 else 0.5 for i in range(window_size)]
    assert len(success_rates) == len(expected_pattern)


def test_performance_trend_tracking(performance_tracker):
    """
    Test performance trend tracking.

    Given: A BatchPerformanceTracker with sequential performance data
    When: Recording metrics with clear trends
    Then: Trends are captured in metrics history
    """
    # Record improving performance trend
    batch_size = 50
    success_rates = [0.6, 0.7, 0.8, 0.9]

    for rate in success_rates:
        successful = int(batch_size * rate)
        failed = batch_size - successful
        performance_tracker.start_batch(batch_size)
        performance_tracker.end_batch(successful, failed, 100.0)

    history = performance_tracker.metrics_history
    # Verify trend is captured
    success_trend = [
        m.successful_objects / (m.successful_objects + m.failed_objects) for m in history
    ]
    assert success_trend == sorted(success_trend)  # Increasing trend


def test_metrics_reset_handling(performance_tracker):
    """
    Test metrics reset and reinitialization.

    Given: A BatchPerformanceTracker with recorded metrics
    When: Metrics are reset
    Then: Tracking system is properly reinitialized
    """
    # Record some initial metrics
    performance_tracker.start_batch(50)
    performance_tracker.end_batch(45, 5, 100.0)

    # Reset metrics
    performance_tracker.reset_performance_metrics()

    # Verify clean state
    assert len(performance_tracker.metrics_history) == 0

    # Verify can record new metrics after reset
    performance_tracker.start_batch(30)
    performance_tracker.end_batch(25, 5, 100.0)

    assert len(performance_tracker.metrics_history) == 1
    latest_metric = performance_tracker.metrics_history[-1]
    assert latest_metric.batch_size == 30
    assert latest_metric.successful_objects == 25
