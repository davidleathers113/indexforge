"""Command-line interface fixtures."""

from argparse import Namespace
from dataclasses import dataclass, field
import logging
import sys
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from ..core.base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class CLIState(BaseState):
    """CLI state management."""

    argv: List[str] = field(default_factory=lambda: sys.argv.copy())
    args_namespace: Optional[Namespace] = None
    module_name: str = "__main__"
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.argv = sys.argv.copy()
        self.args_namespace = None
        self.module_name = "__main__"
        self.error_mode = False

    def set_argv(self, new_argv: List[str]):
        """Set new argv values."""
        self.argv = new_argv

    def set_args(self, **kwargs):
        """Set args namespace values."""
        self.args_namespace = Namespace(**kwargs)


@pytest.fixture(scope="function")
def mock_cli_state():
    """Shared CLI state for testing."""
    state = CLIState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_argparse_parse_args(mock_cli_state):
    """Mock for argparse.ArgumentParser.parse_args with error tracking."""

    def mock_parse_args(*args, **kwargs):
        """Parse args with error handling."""
        try:
            if mock_cli_state.error_mode:
                mock_cli_state.add_error("Argument parsing failed in error mode")
                raise ValueError("Argument parsing failed in error mode")

            if mock_cli_state.args_namespace is None:
                mock_cli_state.add_error("No args namespace configured")
                raise ValueError("No args namespace configured")

            return mock_cli_state.args_namespace

        except Exception as e:
            mock_cli_state.add_error(f"Error parsing arguments: {str(e)}")
            raise

    mock_parse = MagicMock(side_effect=mock_parse_args)
    mock_parse.get_errors = mock_cli_state.get_errors
    mock_parse.reset = mock_cli_state.reset
    mock_parse.set_error_mode = lambda enabled=True: setattr(mock_cli_state, "error_mode", enabled)

    with patch("argparse.ArgumentParser.parse_args", mock_parse):
        yield mock_parse


@pytest.fixture(scope="function")
def mock_sys_argv(mock_cli_state):
    """Mock for sys.argv with state management."""

    def update_argv(new_argv: List[str]):
        """Update argv values."""
        mock_cli_state.set_argv(new_argv)
        sys.argv = mock_cli_state.argv

    original_argv = sys.argv.copy()
    mock_argv = MagicMock()
    mock_argv.__iter__ = lambda self: iter(mock_cli_state.argv)
    mock_argv.__getitem__ = lambda self, i: mock_cli_state.argv[i]
    mock_argv.__len__ = lambda self: len(mock_cli_state.argv)
    mock_argv.update = update_argv
    mock_argv.get_errors = mock_cli_state.get_errors
    mock_argv.reset = mock_cli_state.reset

    with patch.object(sys, "argv", mock_argv):
        yield mock_argv

    sys.argv = original_argv


@pytest.fixture(scope="function")
def mock_name_main(mock_cli_state):
    """Mock for __name__ to simulate command-line entry points."""

    def set_module_name(name: str):
        """Set module name."""
        mock_cli_state.module_name = name

    mock_name = MagicMock()
    mock_name.__str__ = lambda self: mock_cli_state.module_name
    mock_name.__eq__ = lambda self, other: str(mock_cli_state.module_name) == str(other)
    mock_name.set = set_module_name
    mock_name.get_errors = mock_cli_state.get_errors
    mock_name.reset = mock_cli_state.reset

    with patch("src.main.__name__", mock_name):
        yield mock_name
