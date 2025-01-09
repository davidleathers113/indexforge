import os
import pytest
from src.configuration.logger_setup import setup_logger
from tests.fixtures.core.logger import cleanup_logger, temp_log_file

def test_log_rotation(temp_log_file, cleanup_logger):
    """Test log file rotation"""
    max_bytes = 100
    backup_count = 2
    logger = setup_logger('test_logger', temp_log_file, rotate=True, max_bytes=max_bytes, backup_count=backup_count)
    long_message = 'x' * 50
    for _ in range(5):
        logger.info(long_message)
    log_dir = os.path.dirname(temp_log_file)
    backup_files = [f for f in os.listdir(log_dir) if f.startswith(os.path.basename(temp_log_file))]
    assert len(backup_files) <= backup_count + 1

def test_invalid_log_directory():
    """Test handling of invalid log directory"""
    with pytest.raises(Exception):
        setup_logger('test_logger', '/nonexistent/dir/test.log')

def test_logger_cleanup(temp_log_file, cleanup_logger):
    """Test that logger handlers are properly cleaned up"""
    logger1 = setup_logger('test_logger', temp_log_file)
    assert len(logger1.handlers) == 2
    logger2 = setup_logger('test_logger', temp_log_file)
    assert len(logger2.handlers) == 2