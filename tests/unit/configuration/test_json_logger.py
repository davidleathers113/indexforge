import json
import logging
import sys

from src.configuration.logger_setup import JsonFormatter, setup_json_logger


def test_setup_json_logger(temp_log_file, cleanup_logger):
    """Test JSON logger setup"""
    logger = setup_json_logger('test_json_logger', temp_log_file)
    assert logger.name == 'test_json_logger'
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0].formatter, JsonFormatter)


def test_json_formatter():
    """Test JSON formatter output"""
    formatter = JsonFormatter()
    record = logging.LogRecord(name='test_logger', level=logging.INFO, pathname='', lineno=0, msg='Test message', args=(), exc_info=None)
    formatted = formatter.format(record)
    log_data = json.loads(formatted)
    assert 'timestamp' in log_data
    assert log_data['level'] == 'INFO'
    assert log_data['logger'] == 'test_logger'
    assert log_data['message'] == 'Test message'


def test_json_formatter_with_exception():
    """Test JSON formatter with exception information"""
    formatter = JsonFormatter()
    try:
        raise ValueError('Test error')
    except ValueError:
        record = logging.LogRecord(name='test_logger', level=logging.ERROR, pathname='', lineno=0, msg='Error occurred', args=(), exc_info=sys.exc_info())
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        assert 'exception' in log_data
        assert log_data['exception']['type'] == 'ValueError'
        assert 'Traceback' in log_data['exception']['traceback']