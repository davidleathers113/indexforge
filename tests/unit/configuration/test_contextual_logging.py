import json
import logging

from src.configuration.logger_setup import log_with_context, setup_json_logger


def test_log_with_context(temp_log_file, cleanup_logger):
    """Test logging with additional context"""
    logger = setup_json_logger('test_logger', temp_log_file)
    extra_fields = {'user_id': '123', 'action': 'test'}
    log_with_context(logger, logging.INFO, 'Test message', extra_fields)
    with open(temp_log_file) as f:
        log_line = f.read().strip()
        log_data = json.loads(log_line)
        assert log_data['message'] == 'Test message'
        assert log_data['user_id'] == '123'
        assert log_data['action'] == 'test'


def test_log_with_context_no_extra(temp_log_file, cleanup_logger):
    """Test logging without extra context"""
    logger = setup_json_logger('test_logger', temp_log_file)
    log_with_context(logger, logging.INFO, 'Test message')
    with open(temp_log_file) as f:
        log_line = f.read().strip()
        log_data = json.loads(log_line)
        assert log_data['message'] == 'Test message'