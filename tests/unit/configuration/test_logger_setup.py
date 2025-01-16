"""Integration tests for the complete logging system.\n\nThis module contains integration tests that verify different logging components\nwork together correctly, including:\n- Basic and JSON logging\n- Log rotation\n- Contextual logging\n- Performance under load\n"""
import json
import logging
import os
import threading

from src.configuration.logger_setup import log_with_context, setup_json_logger, setup_logger


def test_complete_logging_workflow(temp_log_file, cleanup_logger):
    """Test the complete logging workflow including different formats and rotation"""
    basic_logger = setup_logger('basic_logger', temp_log_file, level=logging.DEBUG)
    basic_logger.debug('Debug message')
    basic_logger.info('Info message')
    with open(temp_log_file) as f:
        log_content = f.read()
        assert 'Debug message' in log_content
        assert 'Info message' in log_content
    json_logger = setup_json_logger('json_logger', temp_log_file)
    context = {'user': 'test_user', 'action': 'integration_test'}
    log_with_context(json_logger, logging.INFO, 'JSON test message', context)
    with open(temp_log_file) as f:
        last_line = f.readlines()[-1].strip()
        log_data = json.loads(last_line)
        assert log_data['message'] == 'JSON test message'
        assert log_data['user'] == 'test_user'
        assert log_data['action'] == 'integration_test'


def test_rotation_with_mixed_logging(temp_log_file, cleanup_logger):
    """Test log rotation works with both basic and JSON logging"""
    max_bytes = 100
    backup_count = 2
    logger = setup_logger('rotating_logger', temp_log_file, rotate=True, max_bytes=max_bytes, backup_count=backup_count)
    long_message = 'x' * 30
    for i in range(10):
        if i % 2 == 0:
            logger.info(f'{long_message} - {i}')
        else:
            log_with_context(logger, logging.INFO, f'{long_message} - {i}', {'count': i})
    log_dir = os.path.dirname(temp_log_file)
    backup_files = [f for f in os.listdir(log_dir) if f.startswith(os.path.basename(temp_log_file))]
    assert len(backup_files) <= backup_count + 1
    for backup_file in backup_files:
        with open(os.path.join(log_dir, backup_file)) as f:
            content = f.read()
            assert content.strip()


def test_concurrent_mixed_logging(temp_log_file, cleanup_logger):
    """Test concurrent logging with mix of basic and JSON formats"""
    basic_logger = setup_logger('basic_concurrent', temp_log_file)
    json_logger = setup_json_logger('json_concurrent', temp_log_file)

    def log_mixed_messages():
        for i in range(5):
            basic_logger.info('Basic message %d', i)
            log_with_context(json_logger, logging.INFO, 'JSON message %d', {'thread': threading.get_ident(), 'count': i})
    threads = [threading.Thread(target=log_mixed_messages) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with open(temp_log_file) as f:
        log_lines = f.readlines()
        basic_logs = [line for line in log_lines if 'Basic message' in line]
        json_logs = [line for line in log_lines if 'JSON message' in line]
        assert len(basic_logs) == 15
        assert len(json_logs) == 15
        for json_log in json_logs:
            log_data = json.loads(json_log)
            assert 'thread' in log_data
            assert 'count' in log_data