"""Pipeline state management fixtures."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from tests.core.base import BaseState

from .logger import logger


@dataclass
class PipelineState(BaseState):
    """Pipeline state management."""

    export_dir: Optional[Path] = None
    index_url: str = "http://localhost:8080"
    log_dir: Optional[Path] = None
    batch_size: int = 100
    error_mode: bool = False
    processed_docs: List[Dict] = field(default_factory=list)

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.processed_docs.clear()
        self.error_mode = False
        self._errors = []  # Initialize errors list

    def add_processed_doc(self, doc: Dict):
        """Add a processed document."""
        logger.debug(f"Adding processed doc: {doc}")
        self.processed_docs.append(doc)
        logger.debug(f"Total processed docs: {len(self.processed_docs)}")

    def add_error(self, error: str):
        """Add an error message."""
        self._errors.append(error)

    def get_errors(self) -> List[str]:
        """Get list of errors."""
        return self._errors


@pytest.fixture(scope="function")
def pipeline_state(tmp_path, request):
    """Shared pipeline state for testing."""
    # Create unique directories for each test using the test name
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    test_dir = tmp_path / test_name
    test_dir.mkdir()

    state = PipelineState(
        export_dir=test_dir / "notion_export",
        log_dir=test_dir / "logs",
    )

    # Create fresh directories
    state.export_dir.mkdir()
    state.log_dir.mkdir()

    yield state

    # Clean up
    state.reset()
    try:
        import shutil

        shutil.rmtree(test_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup test directory {test_dir}: {e}")
