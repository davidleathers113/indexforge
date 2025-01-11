"""Fixtures for utility tests."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pytest

from ..core.base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class SummarizerState(BaseState):
    """Summarizer state management."""

    model_name: str = "facebook/bart-large-cnn"
    max_length: int = 130
    min_length: int = 30
    error_mode: bool = False
    summaries: List[Dict] = field(default_factory=list)

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.summaries.clear()
        self.error_mode = False

    def add_summary(self, text: str, score: float = 0.9):
        """Add a summary result."""
        self.summaries.append(
            {
                "summary_text": text,
                "score": score,
            }
        )

    def get_last_summary(self) -> Optional[Dict]:
        """Get the most recent summary."""
        return self.summaries[-1] if self.summaries else None


@pytest.fixture(scope="function")
def summarizer_state():
    """Shared summarizer state for testing."""
    state = SummarizerState()
    yield state
    state.reset()


@pytest.fixture
def mock_summarizer_pipeline(mocker):
    mock_pipeline = mocker.patch("transformers.pipeline")
    mock_pipeline.return_value = mocker.Mock()
    mock_pipeline.return_value.return_value = [{"summary_text": "Mocked summary"}]
    return mock_pipeline


@pytest.fixture
def mock_cache_manager(mocker):
    mock_cache = mocker.Mock()
    mock_cache.get.return_value = None
    return mock_cache
