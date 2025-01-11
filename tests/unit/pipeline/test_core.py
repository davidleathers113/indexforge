from unittest.mock import Mock, patch
import pandas as pd
import pytest
from src.pipeline.core import Pipeline
from src.pipeline.steps import PipelineStep

@pytest.fixture
def mock_components():
    """Create mock components used by the pipeline"""
    return {'notion': Mock(), 'processor': Mock(), 'indexer': Mock(), 'doc_ops': Mock(), 'search_ops': Mock()}

@pytest.fixture
def pipeline_with_mocks(mock_components, tmp_path):
    """Create a pipeline instance with mocked components"""
    with patch('src.pipeline.core.NotionConnector', return_value=mock_components['notion']), patch('src.pipeline.core.DocumentProcessor', return_value=mock_components['processor']), patch('src.pipeline.core.DocumentIndexer', return_value=mock_components['indexer']), patch('src.pipeline.core.DocumentOperations', return_value=mock_components['doc_ops']), patch('src.pipeline.core.SearchOperations', return_value=mock_components['search_ops']):
        export_dir = tmp_path / 'notion_export'
        export_dir.mkdir()
        pipeline = Pipeline(export_dir=str(export_dir), index_url='http://localhost:8080', log_dir=str(tmp_path / 'logs'), batch_size=100)
        pipeline._mocks = mock_components
        return pipeline

def test_pipeline_initialization(pipeline_with_mocks, tmp_path):
    """Test that pipeline initializes with valid configuration"""
    pipeline = pipeline_with_mocks
    log_dir = tmp_path / 'logs'
    assert log_dir.exists()
    assert pipeline.doc_processor is not None
    assert pipeline.notion is not None
    assert pipeline.pii_detector is not None
    assert pipeline.summarizer is not None
    assert pipeline.embedding_generator is not None
    assert pipeline.topic_clusterer is not None
    assert pipeline.vector_index is not None
    assert pipeline.search_ops is not None
    assert pipeline.doc_ops is not None

def test_pipeline_initialization_invalid_export_dir():
    """Test pipeline initialization with non-existent export directory"""
    with pytest.raises(Exception):
        Pipeline(export_dir='/nonexistent/path')

def test_full_pipeline_execution(pipeline_with_mocks):
    """Test full pipeline execution with all steps"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mock_docs = [{'content': {'body': 'Test document 1'}}, {'content': {'body': 'Test document 2'}}]
    mocks['notion'].load_csv_files.return_value = {'test.csv': pd.DataFrame()}
    mocks['notion'].normalize_data.return_value = mock_docs
    mocks['processor'].process.return_value = mock_docs
    mocks['indexer'].process.return_value = mock_docs
    result = pipeline.process_documents()
    assert len(result) == 2
    mocks['notion'].load_csv_files.assert_called_once()
    mocks['notion'].normalize_data.assert_called_once()
    mocks['processor'].process.assert_called_once()
    mocks['indexer'].process.assert_called_once()

def test_partial_pipeline_execution(pipeline_with_mocks):
    """Test pipeline execution with only specific steps"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mock_docs = [{'content': {'body': 'Test document 1', 'title': 'Test 1'}}]
    mocks['notion'].load_csv_files.return_value = {'test.csv': 'mock_dataframe'}
    mocks['notion'].normalize_data.return_value = mock_docs
    mocks['doc_processor'].batch_documents.return_value = [mock_docs]
    steps = {PipelineStep.LOAD, PipelineStep.SUMMARIZE}
    pipeline.process_documents(steps=steps)
    mocks['notion'].load_csv_files.assert_called_once()
    mocks['notion'].normalize_data.assert_called_once()
    mocks['notion'].normalize_data.assert_called_once()
    mocks['summarizer'].process_documents.assert_called_once()
    mocks['pii_detector'].analyze_document.assert_not_called()
    mocks['embedding_generator'].generate_embeddings.assert_not_called()
    mocks['topic_clusterer'].cluster_documents.assert_not_called()
    mocks['vector_index'].add_documents.assert_not_called()

def test_pipeline_error_handling(pipeline_with_mocks):
    """Test pipeline error handling during execution"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mocks['notion'].load_csv_files.side_effect = Exception('Test error')
    with pytest.raises(Exception) as exc_info:
        pipeline.process_documents()
    assert 'Test error' in str(exc_info.value)

def test_empty_document_handling(pipeline_with_mocks):
    """Test handling of empty or invalid documents"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mock_docs = [{'content': {'body': '', 'title': 'Empty'}}, {'content': {'body': '   ', 'title': 'Whitespace'}}, {'content': {'body': 'Valid', 'title': 'Valid'}}]
    mocks['notion'].load_csv_files.return_value = {'test.csv': 'mock_dataframe'}
    mocks['notion'].normalize_data.return_value = mock_docs
    mocks['doc_processor'].batch_documents.side_effect = lambda x, _: [x]
    result = pipeline.process_documents(steps={PipelineStep.LOAD})
    assert len(result) == 1
    assert result[0]['content']['body'] == 'Valid'

def test_document_batching(pipeline_with_mocks):
    """Test document processing in batches"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mock_docs = [{'content': {'body': f'Doc {i}', 'title': f'Title {i}'}} for i in range(150)]
    mocks['notion'].load_csv_files.return_value = {'test.csv': 'mock_dataframe'}
    mocks['notion'].normalize_data.return_value = mock_docs
    batch1 = mock_docs[:100]
    batch2 = mock_docs[100:]
    mocks['doc_processor'].batch_documents.return_value = [batch1, batch2]
    pipeline.process_documents(steps={PipelineStep.LOAD, PipelineStep.INDEX})
    assert mocks['vector_index'].add_documents.call_count == 2

def test_search_delegation(pipeline_with_mocks):
    """Test search operations are properly delegated"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    expected_result = [{'id': '1', 'score': 0.9}]
    mocks['search_ops'].search.return_value = expected_result
    result = pipeline.search(query='test')
    mocks['search_ops'].search.assert_called_once_with(query='test')
    assert result == expected_result

def test_document_operations_delegation(pipeline_with_mocks):
    """Test document operations are properly delegated"""
    pipeline = pipeline_with_mocks
    mocks = pipeline._mocks
    mocks['doc_ops'].update_document.return_value = True
    mocks['doc_ops'].delete_documents.return_value = True
    update_result = pipeline.update_document(doc_id='1', content='Updated content')
    delete_result = pipeline.delete_documents(doc_ids=['1', '2'])
    mocks['doc_ops'].update_document.assert_called_once_with(doc_id='1', content='Updated content')
    mocks['doc_ops'].delete_documents.assert_called_once_with(doc_ids=['1', '2'])
    assert update_result is True
    assert delete_result is True