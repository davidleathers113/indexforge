"""Fixtures for search tests."""

from dataclasses import dataclass, field
import logging
from unittest.mock import MagicMock

import pytest

from src.indexing.search.search_result import SearchResult

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class SearchState(BaseState):
    """Search executor state."""

    results: list[dict] = field(default_factory=list)
    semantic_score: float = 0.9
    hybrid_score: float = 0.85
    vector_dimensions: int = 3
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        logger.debug("Resetting search state")
        super().reset()
        self.results.clear()
        self.semantic_score = 0.9
        self.hybrid_score = 0.85
        self.error_mode = False
        logger.debug("Search state reset complete")

    def add_result(self, result: dict):
        """Add a search result."""
        logger.debug(f"Adding search result: {result}")
        self.results.append(result)

    def get_default_result(self, index: int = 0) -> SearchResult:
        """Get a default search result."""
        logger.debug(f"Creating default search result with index {index}")
        result = SearchResult(
            id=f"test-id-{index}",
            content={"body": f"Test content {index}"},
            metadata={"title": f"Test {index}"},
            score=self.semantic_score,
            distance=1 - self.semantic_score,
            vector=[0.1 * (i + 1) for i in range(self.vector_dimensions)],
        )
        logger.debug(f"Created default result: {result}")
        return result


@pytest.fixture(scope="function")
def mock_search_executor():
    """Mock search executor for testing."""
    logger.info("Initializing mock search executor")
    mock_executor = MagicMock(name="search_executor")
    state = SearchState()

    def mock_semantic_search(*args, **kwargs) -> list[SearchResult]:
        """Execute semantic search with error tracking."""
        logger.info(f"Executing semantic search with args={args}, kwargs={kwargs}")
        try:
            if state.error_mode:
                error_msg = "Search failed in error mode"
                logger.error(error_msg)
                state.add_error(error_msg)
                raise ValueError(error_msg)

            if not state.results:
                logger.debug("No custom results set, returning default result")
                result = [state.get_default_result()]
                logger.info(f"Returning default result: {result}")
                return result

            logger.info(f"Returning custom results: {state.results}")
            return state.results

        except Exception as e:
            error_msg = f"Error in semantic search: {e!s}"
            logger.error(error_msg, exc_info=True)
            state.add_error(error_msg)
            raise

    def mock_hybrid_search(*args, **kwargs) -> list[SearchResult]:
        """Execute hybrid search with error tracking."""
        logger.info(f"Executing hybrid search with args={args}, kwargs={kwargs}")
        try:
            if state.error_mode:
                error_msg = "Search failed in error mode"
                logger.error(error_msg)
                state.add_error(error_msg)
                raise ValueError(error_msg)

            if not state.results:
                logger.debug("No custom results set, returning default result")
                result = state.get_default_result()
                result.score = state.hybrid_score
                result.distance = 1 - state.hybrid_score
                logger.info(f"Returning default result: {result}")
                return [result]

            logger.info(f"Returning custom results: {state.results}")
            return state.results

        except Exception as e:
            error_msg = f"Error in hybrid search: {e!s}"
            logger.error(error_msg, exc_info=True)
            state.add_error(error_msg)
            raise

    # Configure mock methods
    mock_executor.semantic_search = MagicMock(side_effect=mock_semantic_search)
    mock_executor.hybrid_search = MagicMock(side_effect=mock_hybrid_search)
    mock_executor.get_errors = state.get_errors
    mock_executor.reset = state.reset
    mock_executor.set_error_mode = lambda enabled=True: setattr(state, "error_mode", enabled)
    mock_executor.add_result = state.add_result

    logger.info("Mock search executor initialized")
    yield mock_executor
    logger.debug("Cleaning up mock search executor")
    state.reset()


@pytest.fixture(scope="function")
def mock_search_manager(mock_search_executor):
    """Mock search manager for testing."""
    mock_manager = MagicMock(name="search_manager")

    # Create operations structure
    mock_manager.operations = MagicMock()
    mock_manager.operations.search = mock_search_executor

    # Configure manager to use executor
    mock_manager.executor = mock_search_executor
    mock_manager.get_errors = mock_search_executor.get_errors
    mock_manager.reset = mock_search_executor.reset
    mock_manager.set_error_mode = mock_search_executor.set_error_mode
    mock_manager.add_result = mock_search_executor.add_result

    yield mock_manager
    mock_manager.reset()


@pytest.fixture(scope="function")
def mock_search_components(
    mock_embedding_generator, mock_search_manager, mock_topic_clusterer, mock_logger
):
    """Collection of search-related components for testing."""
    components = {
        "embedding_generator": mock_embedding_generator,
        "vector_index": mock_search_manager,
        "topic_clusterer": mock_topic_clusterer,
        "logger": mock_logger,
    }

    # Add helper to reset all components
    def reset_all():
        for component in components.values():
            if hasattr(component, "reset"):
                component.reset()

    components["reset"] = reset_all
    return components
