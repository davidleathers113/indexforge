"""Tests for performance summary functionality."""
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest
from prometheus_client import REGISTRY
from src.utils.monitoring import PerformanceMetrics, SystemMonitor

@pytest.fixture(autouse=True)
def clear_prometheus_registry():
    """Clear Prometheus registry before each test."""
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    yield

@pytest.fixture
def mock_process():
    """Create a mock psutil Process"""
    with patch('src.utils.monitoring.psutil.Process') as mock:
        mock_instance = Mock()
        memory_info = Mock()
        memory_info.rss = 1024 * 1024 * 100
        mock_instance.memory_info.return_value = memory_info
        mock_instance.cpu_percent.return_value = 50.0
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_logger():
    """Create a mock logger"""
    with patch('logging.getLogger') as mock:
        logger = Mock(spec=logging.Logger)
        mock.return_value = logger
        yield logger

@pytest.fixture
def monitor(mock_process, mock_logger, tmp_path):
    """Create a SystemMonitor instance with mocks"""
    log_path = tmp_path / 'system_metrics.log'
    return SystemMonitor(log_path=str(log_path))

def test_get_performance_summary_empty(monitor):
    """Test performance summary with no metrics"""
    summary = monitor.get_performance_summary()
    assert summary['status'] == 'no_data'
    assert 'period_hours' in summary
    assert 'timestamp' in summary

def test_get_performance_summary_with_data(monitor):
    """Test performance summary with metrics data"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=100.0, memory_mb=200.0, cpu_percent=50.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op'), PerformanceMetrics(latency_ms=150.0, memory_mb=250.0, cpu_percent=60.0, error_count=1, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    summary = monitor.get_performance_summary()
    assert summary['status'] == 'degraded'
    assert 'metrics' in summary
    assert all((key in summary['metrics'] for key in ['latency_ms', 'memory_mb', 'cpu_percent', 'error_count']))

def test_get_performance_summary_time_filter(monitor):
    """Test performance summary time filtering"""
    old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
    new_time = datetime.utcnow().isoformat()
    monitor.performance_history = [PerformanceMetrics(latency_ms=100.0, memory_mb=200.0, cpu_percent=50.0, error_count=0, timestamp=old_time, operation='test_op'), PerformanceMetrics(latency_ms=150.0, memory_mb=250.0, cpu_percent=60.0, error_count=0, timestamp=new_time, operation='test_op')]
    summary = monitor.get_performance_summary(hours=24)
    assert summary['metrics']['latency_ms']['mean'] == 150.0

def test_get_performance_summary_healthy(monitor):
    """Test performance summary with healthy metrics"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=50.0, memory_mb=100.0, cpu_percent=30.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    summary = monitor.get_performance_summary()
    assert summary['status'] == 'healthy'

def test_get_performance_summary_warning(monitor):
    """Test performance summary with warning metrics"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=500.0, memory_mb=100.0, cpu_percent=80.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    summary = monitor.get_performance_summary()
    assert summary['status'] == 'warning'

def test_get_performance_summary_stats(monitor):
    """Test performance summary statistics calculation"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=100.0, memory_mb=200.0, cpu_percent=50.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op'), PerformanceMetrics(latency_ms=200.0, memory_mb=300.0, cpu_percent=60.0, error_count=1, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    summary = monitor.get_performance_summary()
    metrics = summary['metrics']
    for metric in ['latency_ms', 'memory_mb', 'cpu_percent']:
        assert all((key in metrics[metric] for key in ['min', 'max', 'mean', 'std']))
        assert metrics[metric]['min'] <= metrics[metric]['max']
        assert metrics[metric]['std'] >= 0