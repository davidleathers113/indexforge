"""Tests for document validation functionality."""
import pytest
from src.utils.document_processing import DocumentProcessor, DocumentValidationError
from tests.fixtures import mock_doc_processor

def test_validates_valid_document(mock_doc_processor):
    """Test that a valid document passes validation."""
    processor = DocumentProcessor()
    valid_doc = {'content': {'body': 'valid content'}, 'metadata': {'title': 'Test Document'}}
    result = processor.validate(valid_doc)
    assert result is True

def test_rejects_empty_document(mock_doc_processor):
    """Test that an empty document is rejected."""
    processor = DocumentProcessor()
    doc = {}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Missing required field: content' in str(exc_info.value)

def test_rejects_none_content(mock_doc_processor):
    """Test that None content is rejected."""
    processor = DocumentProcessor()
    doc = {'content': None}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid field type: content must be a dictionary' in str(exc_info.value)

def test_rejects_empty_content(mock_doc_processor):
    """Test that empty content is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Missing required field: content.body' in str(exc_info.value)

def test_rejects_missing_body(mock_doc_processor):
    """Test that missing body field is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'wrong_field': 'value'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Missing required field: content.body' in str(exc_info.value)

def test_rejects_non_dict_content(mock_doc_processor):
    """Test that non-dictionary content is rejected."""
    processor = DocumentProcessor()
    doc = {'content': 'not a dict'}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid field type: content must be a dictionary' in str(exc_info.value)

def test_rejects_non_string_body(mock_doc_processor):
    """Test that non-string body is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 123}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid field type: content.body must be a string' in str(exc_info.value)

def test_rejects_non_dict_metadata(mock_doc_processor):
    """Test that non-dictionary metadata is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 'valid'}, 'metadata': 'not a dict'}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid field type: metadata must be a dictionary' in str(exc_info.value)

def test_rejects_content_exceeding_max_length(mock_doc_processor):
    """Test that content exceeding max length is rejected."""
    processor = DocumentProcessor()
    processor.set_max_content_length(100)
    doc = {'content': {'body': 'word ' * 50}, 'metadata': {'title': 'Test'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Content length exceeds maximum' in str(exc_info.value)

def test_rejects_empty_title(mock_doc_processor):
    """Test that empty title is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 'valid content'}, 'metadata': {'title': ''}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid metadata: empty title' in str(exc_info.value)

def test_rejects_null_bytes_in_content(mock_doc_processor):
    """Test that content with null bytes is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': '\x00binary content'}, 'metadata': {'title': 'Test'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid content format: contains null bytes' in str(exc_info.value)

def test_rejects_invalid_unicode_in_content(mock_doc_processor):
    """Test that content with invalid Unicode is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 'unicode \ufffe'}, 'metadata': {'title': 'Test'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid content format: invalid Unicode' in str(exc_info.value)

def test_rejects_ansi_escape_sequences(mock_doc_processor):
    """Test that content with ANSI escape sequences is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': '\x1b[31mcolored text\x1b[0m'}, 'metadata': {'title': 'Test'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid content format: contains ANSI escape sequences' in str(exc_info.value)

def test_rejects_none_in_nested_content(mock_doc_processor):
    """Test that None in nested content is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 'valid', 'sections': {'intro': None}}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid nested structure: content.sections.intro is None' in str(exc_info.value)

def test_rejects_none_in_nested_metadata(mock_doc_processor):
    """Test that None in nested metadata is rejected."""
    processor = DocumentProcessor()
    doc = {'content': {'body': 'valid'}, 'metadata': {'author': {'name': None}}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Invalid nested structure: metadata.author.name is None' in str(exc_info.value)

def test_applies_custom_word_count_rule(mock_doc_processor):
    """Test that custom word count rule is applied."""
    processor = DocumentProcessor()
    processor.add_validation_rule(lambda doc: len(doc['content']['body'].split()) >= 3, 'Document must contain at least 3 words')
    doc = {'content': {'body': 'two words'}, 'metadata': {'title': 'Test'}}
    with pytest.raises(DocumentValidationError) as exc_info:
        processor.validate(doc)
    assert 'Document must contain at least 3 words' in str(exc_info.value)