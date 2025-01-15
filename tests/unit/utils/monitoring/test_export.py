"""Tests for metrics export functionality."""
from datetime import datetime
import json
import logging
from unittest.mock import Mock, mock_open, patch

from prometheus_client import REGISTRY
import pytest

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

def test_export_metrics(monitor):
    """Test metrics export to JSON"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=100.0, memory_mb=200.0, cpu_percent=50.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    with patch('builtins.open', mock_open()) as mock_file:
        monitor.export_metrics('metrics.json')
        mock_file.assert_called_once_with('metrics.json', 'w')
        handle = mock_file()
        written_data = ''.join((call.args[0] for call in handle.write.call_args_list))
        metrics = json.loads(written_data)
        assert 'performance' in metrics
        assert 'errors' in metrics
        assert 'summary' in metrics

def test_export_metrics_empty(monitor):
    """Test metrics export with no data"""
    with patch('builtins.open', mock_open()) as mock_file:
        monitor.export_metrics('empty_metrics.json')
        handle = mock_file()
        written_data = ''.join((call.args[0] for call in handle.write.call_args_list))
        metrics = json.loads(written_data)
        assert metrics['performance'] == []
        assert metrics['errors'] == []
        assert metrics['summary']['status'] == 'no_data'

def test_export_metrics_file_error(monitor):
    """Test handling of file write errors during export"""
    monitor.performance_history = [PerformanceMetrics(latency_ms=100.0, memory_mb=200.0, cpu_percent=50.0, error_count=0, timestamp=datetime.utcnow().isoformat(), operation='test_op')]
    with patch('builtins.open', mock_open()) as mock_file:
        handle = mock_file()
        handle.write.side_effect = IOError('Write error')
        try:
            monitor.export_metrics('error_metrics.json')
        except IOError:
            monitor.logger.error.assert_called_once()
            return
        assert False, 'Expected IOError was not raised'

def test_export_metrics_custom_path(monitor, tmp_path):
    """Test metrics export to custom path"""
    export_path = tmp_path / 'custom'
    export_path.mkdir(parents=True, exist_ok=True)
    metrics_path = export_path / 'metrics.json'
    monitor.export_metrics(str(metrics_path))
    assert metrics_path.exists()

def test_export_metrics_with_errors(monitor):
    """Test metrics export with error history"""
    monitor.error_history = [{'operation': 'test_op', 'error': 'Test error', 'timestamp': datetime.utcnow().isoformat()}]
    with patch('builtins.open', mock_open()) as mock_file:
        monitor.export_metrics('metrics.json')
        handle = mock_file()
        written_data = ''.join((call.args[0] for call in handle.write.call_args_list))
        metrics = json.loads(written_data)
        assert len(metrics['errors']) == 1
        assert metrics['errors'][0]['operation'] == 'test_op'