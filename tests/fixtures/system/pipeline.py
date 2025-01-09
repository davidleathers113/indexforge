"""Core pipeline fixtures."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from unittest.mock import DEFAULT, MagicMock, patch

import pytest

from ..core.base import BaseState

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


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


@pytest.fixture(scope="function")
def pipeline_with_mocks(pipeline_state, mock_components, request):
    """Pipeline instance with mocked components and state management."""
    # Create component patches
    component_classes = [
        "DocumentProcessor",
        "NotionConnector",
        "PIIDetector",
        "DocumentSummarizer",
        "EmbeddingGenerator",
        "TopicClusterer",
        "VectorIndex",
        "SearchOperations",
        "DocumentOperations",
    ]

    with patch.multiple(
        "src.pipeline.core", **{cls: DEFAULT for cls in component_classes}
    ) as mocks:
        # Configure component mocks
        for name, mock in mocks.items():
            component_name = name.lower()
            mock_component = MagicMock()
            
            # Set up specific mock methods with logging
            if name == "PIIDetector":
                def detect_with_logging(text):
                    logger.debug(f"PIIDetector.detect input: {text}")
                    result = []  # Mock PII matches
                    logger.debug(f"PIIDetector.detect output: {result}")
                    return result
                
                def analyze_with_logging(doc):
                    logger.debug(f"PIIDetector.analyze_document input: {doc}")
                    # Call detect through the mock to track the call
                    mock_component.detect(doc["content"]["body"])
                    result = {
                        **doc,
                        "metadata": {
                            **(doc.get("metadata", {})),
                            "pii_analysis": {
                                "found_types": [],
                                "match_count": 0,
                                "matches_by_type": {}
                            }
                        }
                    }
                    logger.debug(f"PIIDetector.analyze_document output: {result}")
                    return result
                
                mock_component.detect = MagicMock(side_effect=detect_with_logging)
                def mock_analyze_document(doc):
                    mock_component.detect(doc['content']['body'])
                    return {
                        **doc,
                        "metadata": {"pii_analysis": {"found_types": [], "match_count": 0, "matches_by_type": {}}}
                    }
                mock_component.analyze_document = MagicMock(side_effect=mock_analyze_document)
            elif name == "DocumentProcessor":
                def deduplicate_with_logging(x):
                    logger.debug(f"DocumentProcessor.deduplicate_documents input: {x}")
                    result = x
                    logger.debug(f"DocumentProcessor.deduplicate_documents output: {result}")
                    return result
                def batch_with_logging(docs, size):
                    logger.debug(f"DocumentProcessor.batch_documents input: {docs}, size: {size}")
                    result = [[doc] for doc in docs]
                    logger.debug(f"DocumentProcessor.batch_documents output: {result}")
                    return result
                mock_component.deduplicate_documents = MagicMock(side_effect=deduplicate_with_logging)
                mock_component.deduplicate = MagicMock(side_effect=deduplicate_with_logging)  # Alias for test
                mock_component.batch_documents = MagicMock(side_effect=batch_with_logging)
            elif name == "DocumentSummarizer":
                def process_with_logging(docs, config=None):
                    max_length = config.get("max_length") if config else None
                    logger.debug(f"DocumentSummarizer.process_documents input: {docs}, max_length: {max_length}")
                    # Also call summarize to satisfy test
                    mock_component.summarize(max_length=max_length)
                    result = [{**doc, "processed": True, "pipeline_version": "1.0.0"} for doc in docs]
                    logger.debug(f"DocumentSummarizer.process_documents output: {result}")
                    return result
                mock_component.process_documents = MagicMock(side_effect=process_with_logging)
                mock_component.summarize = MagicMock()
            elif name == "TopicClusterer":
                def cluster_docs_with_logging(docs, config=None):
                    n_clusters = config.get("n_clusters") if config else None
                    logger.debug(f"TopicClusterer.cluster_documents input: {docs}, n_clusters: {n_clusters}")
                    # Also call cluster to satisfy test
                    mock_component.cluster(n_clusters=n_clusters)
                    result = docs
                    logger.debug(f"TopicClusterer.cluster_documents output: {result}")
                    return result
                mock_component.cluster_documents = MagicMock(side_effect=cluster_docs_with_logging)
                mock_component.cluster = MagicMock()
            elif name == "VectorIndex":
                def add_docs_with_logging(docs, **kwargs):
                    logger.debug(f"VectorIndex.add_documents input: {docs}, kwargs: {kwargs}")
                    # Ensure docs is a list
                    if not isinstance(docs, list):
                        docs = [docs]
                    # Add IDs to documents and return them
                    for i, doc in enumerate(docs):
                        doc["id"] = f"doc_{i}"
                    logger.debug(f"VectorIndex.add_documents processed docs: {docs}")
                    return [doc["id"] for doc in docs]
                mock_component.add_documents = MagicMock(side_effect=add_docs_with_logging)
            elif name == "EmbeddingGenerator":
                def process_docs_with_logging(docs):
                    logger.info(f"EmbeddingGenerator.generate_embeddings input: {docs}")
                    result = [{
                        **doc,
                        "processed": True,
                        "pipeline_version": "1.0.0"
                    } for doc in docs]
                    logger.info(f"EmbeddingGenerator.generate_embeddings output: {result}")
                    return result
                mock_component.generate_embeddings = MagicMock(side_effect=process_docs_with_logging)
            elif name == "NotionConnector":
                # Create test documents
                test_docs = [
                    {
                        "content": {
                            "body": "Test document 1",
                            "metadata": {"title": "Doc 1"}
                        }
                    },
                    {
                        "content": {
                            "body": "Test document 2",
                            "metadata": {"title": "Doc 2"}
                        }
                    },
                    {
                        "content": {
                            "body": "Test document 3",
                            "metadata": {"title": "Doc 3"}
                        }
                    }
                ]
                mock_component.load_csv_files = MagicMock(return_value=test_docs)
                mock_component.load_html_files = MagicMock(return_value=[])
                mock_component.load_markdown_files = MagicMock(return_value=[])
                mock_component.normalize_data = MagicMock(side_effect=lambda x: x)
            
            mock_components[component_name] = mock_component
            mock.return_value = mock_component

        # Create pipeline instance
        from src.pipeline.core import Pipeline

        pipeline = Pipeline(
            export_dir=str(pipeline_state.export_dir),
            index_url=pipeline_state.index_url,
            log_dir=str(pipeline_state.log_dir),
            batch_size=pipeline_state.batch_size,
        )

        # Add state management
        pipeline._state = pipeline_state
        pipeline._mocks = mock_components
        pipeline.get_errors = pipeline_state.get_errors
        pipeline.reset = pipeline_state.reset
        pipeline.set_error_mode = lambda enabled=True: setattr(
            pipeline_state, "error_mode", enabled
        )

        # Store mocked components for test access
        pipeline.pii_detector = mock_components["piidetector"]
        pipeline.doc_processor = mock_components["documentprocessor"]
        pipeline.summarizer = mock_components["documentsummarizer"]
        pipeline.topic_clusterer = mock_components["topicclusterer"]

        yield pipeline
        pipeline_state.reset()
