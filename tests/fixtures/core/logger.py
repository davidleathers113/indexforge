"""Logger fixtures for testing."""

from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from .base import BaseState


@dataclass
class LoggerState(BaseState):
    """Logger state management."""

    messages: List[Dict] = field(default_factory=list)
    log_level: int = logging.INFO
    log_format: str = "%(levelname)s - %(message)s"
    capture_output: bool = True
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.messages.clear()
        self.log_level = logging.INFO
        self.capture_output = True
        self.error_mode = False

    def add_message(self, level: int, msg: str, **kwargs):
        """Add a log message with metadata."""
        self.messages.append(
            {
                "level": level,
                "level_name": logging.getLevelName(level),
                "message": msg,
                "metadata": kwargs,
                "timestamp": kwargs.get("created", None),
            }
        )

    def get_messages(self, level: Optional[int] = None) -> List[Dict]:
        """Get filtered log messages."""
        if level is None:
            return self.messages.copy()
        return [m for m in self.messages if m["level"] == level]


@pytest.fixture(scope="function")
def logger_state():
    """Shared logger state for testing."""
    state = LoggerState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_logger(logger_state):
    """Mock logger with state management."""
    mock_log = MagicMock()

    def create_log_method(level: int):
        """Create a logging method for the given level."""

        def log_method(msg: str, *args, **kwargs):
            try:
                if logger_state.error_mode and level >= logging.ERROR:
                    logger_state.add_error("Logging failed in error mode: %s" % msg)
                    raise ValueError("Logging failed in error mode: %s" % msg)

                if logger_state.capture_output:
                    logger_state.add_message(level, msg, **kwargs)

                if args:
                    msg = msg % args
                if level >= logger_state.log_level:
                    print("%s - %s" % (logging.getLevelName(level), msg))

            except Exception as e:
                logger_state.add_error("Error logging message: %s" % str(e))
                raise

        return log_method

    # Configure logging methods
    mock_log.debug = MagicMock(side_effect=create_log_method(logging.DEBUG))
    mock_log.info = MagicMock(side_effect=create_log_method(logging.INFO))
    mock_log.warning = MagicMock(side_effect=create_log_method(logging.WARNING))
    mock_log.error = MagicMock(side_effect=create_log_method(logging.ERROR))
    mock_log.critical = MagicMock(side_effect=create_log_method(logging.CRITICAL))

    # Add helper methods
    mock_log.get_messages = logger_state.get_messages
    mock_log.get_errors = logger_state.get_errors
    mock_log.reset = logger_state.reset
    mock_log.set_level = lambda level: setattr(logger_state, "log_level", level)
    mock_log.set_capture = lambda enabled=True: setattr(logger_state, "capture_output", enabled)
    mock_log.set_error_mode = lambda enabled=True: setattr(logger_state, "error_mode", enabled)

    yield mock_log
    logger_state.reset()


@pytest.fixture(scope="function")
def temp_log_file(tmp_path):
    """Create a temporary log file path."""
    log_path = tmp_path / "test.log"
    yield str(log_path)
    if log_path.exists():
        log_path.unlink()


@pytest.fixture(scope="function")
def file_logger(temp_log_file, logger_state):
    """Logger that writes to a file with state management."""
    # Configure file handler
    handler = logging.FileHandler(temp_log_file)
    handler.setFormatter(logging.Formatter(logger_state.log_format))
    handler.setLevel(logger_state.log_level)

    # Create logger
    logger = logging.getLogger("test_file_logger")
    logger.setLevel(logger_state.log_level)
    logger.addHandler(handler)

    # Add state management methods
    logger.get_messages = logger_state.get_messages
    logger.get_errors = logger_state.get_errors
    logger.reset = logger_state.reset
    logger.set_level = lambda level: setattr(logger_state, "log_level", level)

    yield logger

    # Cleanup
    logger.removeHandler(handler)
    handler.close()
    logger_state.reset()


@pytest.fixture(scope="function")
def cleanup_logger():
    """Clean up root logger after each test."""
    yield
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
