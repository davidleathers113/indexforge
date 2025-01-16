"""Tests for main module execution flow.

This module focuses on testing the pipeline initialization and execution flow.
Other aspects are tested in:
- test_validation.py - Tests parameter validation rules
- test_parameters.py - Tests parameter handling edge cases
- test_run_pipeline.py - Tests CLI functionality
"""
from pathlib import Path
from unittest.mock import ANY

import pytest

from src.main import run_pipeline
from src.pipeline.errors import PipelineError


def test_pipeline_execution(pipeline_with_mocks):
    """Test that pipeline executes document processing."""
    pipeline = pipeline_with_mocks
    result = pipeline.process_documents()
    assert len(result) > 0
    for doc in result:
        assert doc.get('processed') is True
        assert doc.get('pipeline_version') == '1.0.0'


def test_pipeline_options(pipeline_with_mocks):
    """Test that pipeline accepts and uses options correctly."""
    pipeline = pipeline_with_mocks
    options = {'detect_pii': True, 'deduplicate': True, 'summary_config': {'max_length': 100}, 'cluster_config': {'n_clusters': 5}}
    pipeline.process_documents(**options)
    pipeline.topic_clusterer.cluster_documents.assert_called_with(ANY, {'n_clusters': 5})
    pipeline.summarizer.process_documents.assert_called_with(ANY, {'max_length': 100})
    assert pipeline.doc_processor.deduplicate_documents.called
    assert pipeline.pii_detector.analyze_document.called


def test_pipeline_error_handling(pipeline_with_mocks, tmp_path):
    """Test that pipeline handles errors properly."""
    export_dir = tmp_path / 'notion_export'
    export_dir.mkdir()
    pipeline = run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', log_dir=str(tmp_path / 'logs'), batch_size=100)
    pipeline.process_documents = lambda **kwargs: (_ for _ in ()).throw(PipelineError('Pipeline processing failed'))
    with pytest.raises(PipelineError) as exc_info:
        pipeline.process_documents()
    assert 'Pipeline processing failed' in str(exc_info.value)


def test_pipeline_initialization_with_defaults(pipeline_with_mocks, tmp_path):
    """Test that pipeline is initialized with default parameters."""
    export_dir = tmp_path / 'notion_export'
    export_dir.mkdir()
    pipeline = run_pipeline(export_dir=str(export_dir), index_url='http://localhost:8080')
    assert pipeline._export_dir == Path(export_dir)
    assert pipeline._index_url == 'http://localhost:8080'
    assert pipeline._log_dir == Path('logs')
    assert pipeline._batch_size == 100
    assert pipeline.doc_processor is not None
    assert pipeline.notion is not None
    assert pipeline.pii_detector is not None
    assert pipeline.summarizer is not None
    assert pipeline.embedding_generator is not None
    assert pipeline.topic_clusterer is not None
    assert pipeline.vector_index is not None
    assert pipeline.search_ops is not None
    assert pipeline.doc_ops is not None