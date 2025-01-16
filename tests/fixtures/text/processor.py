"""Text processing fixtures for testing."""

from dataclasses import dataclass, field
import logging
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class TextState(BaseState):
    """Text processing state."""

    max_tokens: int = 1000
    encoding_name: str = "cl100k_base"
    error_mode: bool = False
    processed_texts: list[str] = field(default_factory=list)

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.max_tokens = 1000
        self.encoding_name = "cl100k_base"
        self.error_mode = False
        self.processed_texts.clear()

    def add_processed_text(self, text: str):
        """Add a processed text to history."""
        self.processed_texts.append(text)


@pytest.fixture(scope="function")
def text_state():
    """Shared text processing state."""
    state = TextState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_encoding(text_state):
    """Mock text encoding."""
    mock_enc = MagicMock()

    def mock_encode(text: str) -> list[int]:
        """Encode text to tokens."""
        try:
            if text_state.error_mode:
                text_state.add_error("Encoding failed in error mode")
                raise ValueError("Encoding failed in error mode")

            # Simple encoding simulation
            words = text.split()
            tokens = list(range(len(words)))  # Simulate token IDs
            text_state.add_processed_text(text)
            return tokens

        except Exception as e:
            text_state.add_error(str(e))
            raise

    def mock_decode(tokens: list[int]) -> str:
        """Decode tokens to text."""
        try:
            if text_state.error_mode:
                text_state.add_error("Decoding failed in error mode")
                raise ValueError("Decoding failed in error mode")

            # Simple decoding simulation
            return " ".join([f"word{t}" for t in tokens])

        except Exception as e:
            text_state.add_error(str(e))
            raise

    # Configure mock methods
    mock_enc.encode = MagicMock(side_effect=mock_encode)
    mock_enc.decode = MagicMock(side_effect=mock_decode)
    mock_enc.get_errors = text_state.get_errors
    mock_enc.reset = text_state.reset
    mock_enc.set_error_mode = lambda enabled=True: setattr(text_state, "error_mode", enabled)

    yield mock_enc
    text_state.reset()


@pytest.fixture(scope="function")
def mock_tiktoken(text_state):
    """Mock tiktoken for testing."""
    mock_tok = MagicMock()

    def mock_get_encoding(name: str):
        """Get encoding by name."""
        try:
            if text_state.error_mode:
                text_state.add_error(f"Failed to get encoding {name}")
                raise ValueError(f"Failed to get encoding {name}")

            if name != text_state.encoding_name:
                text_state.add_error(f"Unknown encoding {name}")
                raise ValueError(f"Unknown encoding {name}")

            return MagicMock(
                encode=lambda text: list(range(len(text.split()))),
                decode=lambda tokens: " ".join([f"word{t}" for t in tokens]),
            )

        except Exception as e:
            text_state.add_error(str(e))
            raise

    # Configure mock methods
    mock_tok.get_encoding = MagicMock(side_effect=mock_get_encoding)
    mock_tok.get_errors = text_state.get_errors
    mock_tok.reset = text_state.reset
    mock_tok.set_error_mode = lambda enabled=True: setattr(text_state, "error_mode", enabled)

    yield mock_tok
    text_state.reset()
