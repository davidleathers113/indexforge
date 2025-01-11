"""Tests for the document loader component."""
import uuid
from unittest.mock import patch
import pytest
from src.pipeline.components.loader import DocumentLoader
from src.pipeline.config.settings import PipelineConfig

@pytest.fixture
def config():
    """Create a test configuration."""
    return PipelineConfig(export_dir='test_dir', min_document_length=10)

@pytest.fixture
def mock_notion():
    """Create a mock NotionConnector."""
    with patch('src.pipeline.components.loader.NotionConnector') as mock:
        instance = mock.return_value
        instance.load_csv_files.return_value = []
        instance.load_html_files.return_value = []
        instance.load_markdown_files.return_value = []
        yield instance

@pytest.fixture
def loader(config, mock_notion):
    """Create a test loader."""
    return DocumentLoader(config=config)

def test_loader_initialization(config, mock_notion):
    """Test loader initialization."""
    loader = DocumentLoader(config=config)
    assert loader.config == config
    mock_notion.assert_called_once_with(str(config.export_dir))

def test_loader_process_empty(loader):
    """Test processing with no documents."""
    result = loader.process()
    assert result == []

def test_loader_process_csv_files(loader, mock_notion):
    """Test processing CSV files."""
    csv_docs = [{'content': {'body': 'test content'}}]
    mock_notion.load_csv_files.return_value = csv_docs
    mock_notion.normalize_data.return_value = csv_docs
    result = loader.process()
    assert len(result) == 1
    assert 'id' in result[0]
    assert result[0]['content']['body'] == 'test content'

def test_loader_process_html_files(loader, mock_notion):
    """Test processing HTML files."""
    html_docs = [{'content': {'body': 'test content'}}]
    mock_notion.load_html_files.return_value = html_docs
    result = loader.process()
    assert len(result) == 1
    assert 'id' in result[0]
    assert result[0]['content']['body'] == 'test content'

def test_loader_process_markdown_files(loader, mock_notion):
    """Test processing Markdown files."""
    md_docs = [{'content': {'body': 'test content'}}]
    mock_notion.load_markdown_files.return_value = md_docs
    result = loader.process()
    assert len(result) == 1
    assert 'id' in result[0]
    assert result[0]['content']['body'] == 'test content'

def test_loader_uuid_generation(loader, mock_notion):
    """Test UUID generation for documents."""
    docs = [{'content': {'body': 'test content'}}]
    mock_notion.load_markdown_files.return_value = docs
    with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
        result = loader.process()
        assert result[0]['id'] == '12345678-1234-5678-1234-567812345678'

def test_loader_filter_invalid_documents(loader, mock_notion):
    """Test filtering of invalid documents."""
    docs = [{'content': {'body': ''}}, {'content': {'body': 'short'}}, {'content': {'body': '```code block```'}}, {'content': {'body': '```mermaid\ngraph TD;```'}}, {'content': {'body': 'valid document content'}}]
    mock_notion.load_markdown_files.return_value = docs
    result = loader.process()
    assert len(result) == 1
    assert result[0]['content']['body'] == 'valid document content'

def test_loader_combine_all_sources(loader, mock_notion):
    """Test combining documents from all sources."""
    csv_docs = [{'content': {'body': 'csv content'}}]
    html_docs = [{'content': {'body': 'html content'}}]
    md_docs = [{'content': {'body': 'markdown content'}}]
    mock_notion.load_csv_files.return_value = csv_docs
    mock_notion.normalize_data.return_value = csv_docs
    mock_notion.load_html_files.return_value = html_docs
    mock_notion.load_markdown_files.return_value = md_docs
    result = loader.process()
    assert len(result) == 3
    contents = {doc['content']['body'] for doc in result}
    assert contents == {'csv content', 'html content', 'markdown content'}