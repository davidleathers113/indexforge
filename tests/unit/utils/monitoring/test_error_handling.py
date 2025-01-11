'Tests for error handling in monitoring.'
import logging
from unittest.mock import Mock, patch
import pytest
from src.utils.monitoring import SystemMonitor

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
def mock_prometheus():
    """Create mock Prometheus metrics"""
    with patch('src.utils.monitoring.Counter') as counter_mock, patch('src.utils.monitoring.Histogram') as histogram_mock, patch('src.utils.monitoring.Gauge') as gauge_mock:
        counter = Mock()
        counter.inc = Mock()
        counter_mock.return_value = counter
        histogram = Mock()
        histogram.observe = Mock()
        histogram_mock.return_value = histogram
        gauge = Mock()
        gauge.set = Mock()
        gauge_mock.return_value = gauge
        yield {'counter': counter, 'histogram': histogram, 'gauge': gauge}

@pytest.fixture
def mock_logger():
    """Create a mock logger"""
    with patch('logging.getLogger') as mock:
        logger = Mock(spec=logging.Logger)
        mock.return_value = logger
        yield logger

@pytest.fixture
def monitor(mock_process, mock_prometheus, mock_logger, tmp_path):
    """Create a SystemMonitor instance with mocks"""
    log_path = tmp_path / 'system_metrics.log'
    return SystemMonitor(log_path=str(log_path))

def test_system_metrics_error(monitor, mock_process):
    """Test handling of system metrics collection error"""
    mock_process.memory_info.side_effect = Exception('Memory info error')

    @monitor.track_operation('test_op')
    def test_function():
        return 'success'
    result = test_function()
    assert result == 'success'
    assert len(monitor.error_history) == 0
    assert len(monitor.performance_history) == 1

def test_prometheus_metrics_error(monitor, mock_prometheus):
    """Test handling of Prometheus metrics error"""
    mock_prometheus['counter'].inc.side_effect = Exception('Prometheus error')

    @monitor.track_operation('test_op')
    def test_function():
        return 'success'
    result = test_function()
    assert result == 'success'
    assert monitor.logger.error.called
    assert len(monitor.error_history) == 0

def test_operation_error_handling(monitor):
    """Test handling of operation errors"""
    error_message = 'Operation failed'

    @monitor.track_operation('test_op')
    def test_function():
        raise ValueError(error_message)
    with pytest.raises(ValueError, match=error_message):
        test_function()
    assert len(monitor.error_history) == 1
    error_record = monitor.error_history[0]
    assert error_record['operation'] == 'test_op'
    assert error_message in error_record['error']
    assert 'timestamp' in error_record

def test_concurrent_error_handling(monitor):
    """Test error handling with concurrent operations"""
    import threading

    @monitor.track_operation('thread_op')
    def thread_function():
        raise ValueError('Thread error')
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=lambda: pytest.raises(ValueError, thread_function))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    assert len(monitor.error_history) == 3
    assert all((record['operation'] == 'thread_op' for record in monitor.error_history))

def test_error_history_limit(monitor):
    """Test error history size limit"""
    monitor.max_history = 2

    @monitor.track_operation('test_op')
    def test_function():
        raise ValueError('Test error')
    for _ in range(3):
        with pytest.raises(ValueError):
            test_function()
    assert len(monitor.error_history) == 2

def test_error_context_capture(monitor):
    """Test error context information capture"""

    @monitor.track_operation('test_op')
    def test_function(arg1, arg2):
        raise ValueError('Error with %s and %s' % (arg1, arg2))
    with pytest.raises(ValueError):
        test_function('value1', 'value2')
    error_record = monitor.error_history[0]
    assert 'value1' in error_record['error']
    assert 'value2' in error_record['error']
    assert error_record['operation'] == 'test_op'