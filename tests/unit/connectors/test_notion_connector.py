import pytest
import pandas as pd
from src.connectors.notion_connector import NotionConnector

@pytest.fixture
def mock_csv_data():
    """Create mock CSV data"""
    return pd.DataFrame({'Name': ['Test Page 1', 'Test Page 2'], 'Content': ['Content 1', 'Content 2'], 'Created time': ['2024-01-01T00:00:00', '2024-01-02T00:00:00'], 'Last edited time': ['2024-01-01T01:00:00', '2024-01-02T01:00:00']})

@pytest.fixture
def mock_html_content():
    """Create mock HTML content"""
    return '\n    <html>\n        <head><title>Test Page</title></head>\n        <body>\n            <article>\n                <h1>Test Content</h1>\n                <p>This is test content.</p>\n            </article>\n        </body>\n    </html>\n    '

@pytest.fixture
def mock_markdown_content():
    """Create mock Markdown content"""
    return '# Test Title\n    \nThis is test content in markdown format.\n- Point 1\n- Point 2\n    '

@pytest.fixture
def connector(tmp_path):
    """Create a NotionConnector instance with temporary directory"""
    return NotionConnector(export_path=str(tmp_path))

def test_load_csv_files(connector, mock_csv_data, tmp_path):
    """Test loading CSV files"""
    csv_path = tmp_path / 'test.csv'
    mock_csv_data.to_csv(csv_path, index=False)
    all_csv_path = tmp_path / 'test_all.csv'
    mock_csv_data.to_csv(all_csv_path, index=False)
    result = connector.load_csv_files()
    assert len(result) == 1
    assert 'test' in result
    assert isinstance(result['test'], pd.DataFrame)
    assert len(result['test']) == 2

def test_load_csv_files_empty_directory(connector):
    """Test loading CSV files from empty directory"""
    result = connector.load_csv_files()
    assert result == {}

def test_load_csv_files_malformed(connector, tmp_path):
    """Test loading malformed CSV files"""
    csv_path = tmp_path / 'malformed.csv'
    csv_path.write_text('invalid,csv\ndata')
    with pytest.raises(pd.errors.EmptyDataError):
        connector.load_csv_files()

def test_load_html_files(connector, mock_html_content, tmp_path):
    """Test loading HTML files"""
    html_path = tmp_path / 'test.html'
    html_path.write_text(mock_html_content)
    result = connector.load_html_files()
    assert len(result) == 1
    doc = result[0]
    assert doc['metadata']['title'] == 'Test Page'
    assert 'This is test content' in doc['content']['body']
    assert doc['metadata']['source'] == 'notion'

def test_load_html_files_no_title(connector, tmp_path):
    """Test loading HTML files without title"""
    html_content = '<html><body><article>Test content</article></body></html>'
    html_path = tmp_path / 'test.html'
    html_path.write_text(html_content)
    result = connector.load_html_files()
    assert len(result) == 1
    assert result[0]['metadata']['title'] == 'test'

def test_load_html_files_no_content(connector, tmp_path):
    """Test loading HTML files without main content"""
    html_content = '<html><body>No article or main</body></html>'
    html_path = tmp_path / 'test.html'
    html_path.write_text(html_content)
    result = connector.load_html_files()
    assert len(result) == 1
    assert result[0]['content']['body'] == ''

def test_load_markdown_files(connector, mock_markdown_content, tmp_path):
    """Test loading Markdown files"""
    md_path = tmp_path / 'test.md'
    md_path.write_text(mock_markdown_content)
    result = connector.load_markdown_files()
    assert len(result) == 1
    doc = result[0]
    assert doc['metadata']['title'] == 'Test Title'
    assert 'Point 1' in doc['content']['body']
    assert doc['metadata']['source'] == 'notion'

def test_load_markdown_files_no_title(connector, tmp_path):
    """Test loading Markdown files without title"""
    content = 'This is content without a title'
    md_path = tmp_path / 'test.md'
    md_path.write_text(content)
    result = connector.load_markdown_files()
    assert len(result) == 1
    assert result[0]['metadata']['title'] == 'test'

def test_load_markdown_files_empty(connector, tmp_path):
    """Test loading empty Markdown files"""
    md_path = tmp_path / 'empty.md'
    md_path.write_text('')
    result = connector.load_markdown_files()
    assert len(result) == 1
    assert result[0]['content']['body'] == ''

def test_normalize_data(connector, mock_csv_data):
    """Test data normalization from dataframes"""
    dataframes = {'test': mock_csv_data}
    result = connector.normalize_data(dataframes)
    assert len(result) == 2
    for doc in result:
        assert 'metadata' in doc
        assert 'content' in doc
        assert 'relationships' in doc
        assert 'embeddings' in doc
        assert doc['metadata']['source'] == 'notion'

def test_normalize_data_missing_fields(connector):
    """Test normalization with missing fields"""
    df = pd.DataFrame({'Name': ['Test']})
    result = connector.normalize_data({'test': df})
    assert len(result) == 1
    doc = result[0]
    assert doc['metadata']['title'] == 'Test'
    assert doc['content']['body'] == ''

def test_normalize_data_empty_dataframe(connector):
    """Test normalization with empty dataframe"""
    df = pd.DataFrame()
    result = connector.normalize_data({'test': df})
    assert result == []

def test_process_export(connector, mock_csv_data, mock_html_content, mock_markdown_content, tmp_path):
    """Test full export processing"""
    csv_path = tmp_path / 'test.csv'
    mock_csv_data.to_csv(csv_path, index=False)
    html_path = tmp_path / 'test.html'
    html_path.write_text(mock_html_content)
    md_path = tmp_path / 'test.md'
    md_path.write_text(mock_markdown_content)
    result = connector.process_export()
    assert len(result) == 4
    assert all((isinstance(doc, dict) for doc in result))
    assert all((doc['metadata']['source'] == 'notion' for doc in result))

def test_process_export_no_files(connector):
    """Test processing export with no files"""
    result = connector.process_export()
    assert result == []

def test_file_permission_error(connector, tmp_path):
    """Test handling of file permission errors"""
    path = tmp_path / 'noaccess.csv'
    path.touch()
    path.chmod(0)
    result = connector.process_export()
    assert result == []
    path.chmod(438)

def test_unicode_error_handling(connector, tmp_path):
    """Test handling of Unicode decode errors"""
    path = tmp_path / 'test.md'
    with open(path, 'wb') as f:
        f.write(b'\x80invalid unicode')
    result = connector.process_export()
    assert result == []

def test_nested_directory_structure(connector, tmp_path):
    """Test processing nested directory structure"""
    nested_dir = tmp_path / 'dir1' / 'dir2'
    nested_dir.mkdir(parents=True)
    md_path = nested_dir / 'test.md'
    md_path.write_text('# Test')
    result = connector.process_export()
    assert len(result) == 1
    assert 'dir1/dir2' in result[0]['metadata']['path']

def test_mixed_file_types(connector, tmp_path):
    """Test processing mixed file types in same directory"""
    (tmp_path / 'test1.csv').write_text('Name,Content\nTest,Content')
    (tmp_path / 'test2.html').write_text('<html><body>Test</body></html>')
    (tmp_path / 'test3.md').write_text('# Test')
    result = connector.process_export()
    assert len(result) == 3
    file_types = {doc['metadata']['path'].split('.')[-1] for doc in result}
    assert file_types == {'csv', 'html', 'md'}

def test_large_file_handling(connector, tmp_path):
    """Test handling of large files"""
    large_content = '# Large File\n' + 'Test content\n' * 10000
    md_path = tmp_path / 'large.md'
    md_path.write_text(large_content)
    result = connector.process_export()
    assert len(result) == 1
    assert len(result[0]['content']['body']) > 50000