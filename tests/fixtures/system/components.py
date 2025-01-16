"""Component collection fixtures."""

from dataclasses import dataclass, field
import logging
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class ComponentState(BaseState):
    """Component collection state."""

    components: dict[str, MagicMock] = field(default_factory=dict)
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.components.clear()
        self.error_mode = False

    def add_component(self, name: str, component: MagicMock):
        """Add a component to the collection."""
        self.components[name] = component

    def get_component(self, name: str) -> MagicMock | None:
        """Get a component by name."""
        return self.components.get(name)


@pytest.fixture(scope="function")
def component_state():
    """Shared component state for testing."""
    state = ComponentState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_components(
    component_state,
    mock_doc_processor,
    mock_pii_detector,
    mock_topic_clusterer,
    mock_embedding_generator,
    mock_search_manager,
    mock_summarizer_pipeline,
    doc_state,
):
    """Collection of pipeline component mocks with state management."""
    # Add real mocks
    component_state.add_component("documentprocessor", mock_doc_processor)
    component_state.add_component("piidetector", mock_pii_detector)
    component_state.add_component("topicclusterer", mock_topic_clusterer)
    component_state.add_component("embeddinggenerator", mock_embedding_generator)
    component_state.add_component("vectorindex", mock_search_manager)

    # Create NotionConnector mock with test documents
    notion_mock = MagicMock(name="notionconnector")

    def load_csv_files():
        return [doc_state.create_document(content="Test CSV content")]

    def load_html_files():
        return [doc_state.create_document(content="Test HTML content")]

    def load_markdown_files():
        return [doc_state.create_document(content="Test Markdown content")]
    notion_mock.load_csv_files = MagicMock(side_effect=load_csv_files)
    notion_mock.load_html_files = MagicMock(side_effect=load_html_files)
    notion_mock.load_markdown_files = MagicMock(side_effect=load_markdown_files)
    notion_mock.normalize_data = lambda x: x  # Pass through data unchanged
    component_state.add_component("notionconnector", notion_mock)

    # Create other simple mocks
    def create_mock(name: str):
        mock = MagicMock(name=name)
        mock.get_errors = component_state.get_errors
        mock.reset = component_state.reset
        mock.set_error_mode = lambda enabled=True: setattr(component_state, "error_mode", enabled)
        return mock

    # Add other simple mocks
    for name in [
        "searchoperations",
        "documentoperations"
    ]:
        component_state.add_component(name, create_mock(name))

    # Add summarizer mock
    component_state.add_component("documentsummarizer", mock_summarizer_pipeline)

    # Add helper methods to the collection
    components = component_state.components.copy()
    components["get_errors"] = component_state.get_errors
    components["reset"] = component_state.reset
    components["set_error_mode"] = lambda enabled=True: setattr(
        component_state, "error_mode", enabled
    )

    yield components
    component_state.reset()
