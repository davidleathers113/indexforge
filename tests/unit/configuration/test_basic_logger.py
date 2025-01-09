import logging
import pytest
from src.configuration.logger_setup import setup_logger
from tests.fixtures.core.logger import cleanup_logger, temp_log_file

def test_setup_logger_basic(temp_log_file, cleanup_logger):
    """Test basic logger setup with default parameters"""
    logger = setup_logger('test_logger', temp_log_file)
    assert logger.name == 'test_logger'
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2
    assert any((isinstance(h, logging.StreamHandler) for h in logger.handlers))
    assert any((isinstance(h, logging.FileHandler) for h in logger.handlers))

def test_setup_logger_custom_level(temp_log_file, cleanup_logger):
    """Test logger setup with custom log level"""
    logger = setup_logger('test_logger', temp_log_file, level=logging.DEBUG)
    assert logger.level == logging.DEBUG

def test_setup_logger_custom_format(temp_log_file, cleanup_logger):
    """Test logger setup with custom format"""
    format_string = '%(levelname)s - %(message)s'
    logger = setup_logger('test_logger', temp_log_file, format_string=format_string)
    logger.info('Test message')
    with open(temp_log_file, 'r') as f:
        log_line = f.read().strip()
        assert 'INFO - Test message' in log_line

def test_setup_logger_no_file(cleanup_logger):
    """Test logger setup without file handler"""
    logger = setup_logger('test_logger')
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)