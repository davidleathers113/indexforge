"""Mock pipeline fixtures."""

from typing import Dict, List
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="function")
def mock_pipeline(pipeline_state):
    """Mock pipeline with state management."""
    mock_pipe = MagicMock()

    def mock_process_documents(docs: List[Dict], **kwargs) -> List[Dict]:
        """Process documents with error tracking."""
        try:
            if pipeline_state.error_mode:
                pipeline_state.add_error("Pipeline processing failed in error mode")
                raise ValueError("Pipeline processing failed in error mode")

            for doc in docs:
                processed = {
                    **doc,
                    "processed": True,
                    "pipeline_version": "1.0.0",
                }
                pipeline_state.add_processed_doc(processed)

            return pipeline_state.processed_docs

        except Exception as e:
            pipeline_state.add_error(f"Error processing documents: {str(e)}")
            raise

    # Configure mock methods
    mock_pipe.process_documents = MagicMock(side_effect=mock_process_documents)
    mock_pipe.get_errors = pipeline_state.get_errors
    mock_pipe.reset = pipeline_state.reset
    mock_pipe.set_error_mode = lambda enabled=True: setattr(pipeline_state, "error_mode", enabled)

    yield mock_pipe
    pipeline_state.reset()
