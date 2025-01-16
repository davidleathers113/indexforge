"""Tests for basic document processing operations."""
import pytest

from src.utils.document_processing import DocumentProcessor


def test_process_document(mock_doc_processor, sample_document):
    """Test basic document processing."""
    processor = DocumentProcessor()
    result = processor.process(sample_document)
    assert result['processed'] is True
    assert 'content' in result
    assert 'metadata' in result
    assert result['metadata']['word_count'] > 0
    assert result['metadata']['chunk_count'] > 0


def test_process_empty_document(mock_doc_processor):
    """Test processing empty document."""
    processor = DocumentProcessor()
    empty_doc = {'content': {'body': ''}}
    with pytest.raises(ValueError, match='Empty document content'):
        processor.process(empty_doc)


def test_process_invalid_document(mock_doc_processor):
    """Test processing invalid document."""
    processor = DocumentProcessor()
    invalid_doc = {'invalid': 'format'}
    with pytest.raises(ValueError, match='Missing content in document'):
        processor.process(invalid_doc)


def test_chunk_size_configuration(mock_doc_processor):
    """Test chunk size configuration."""
    processor = DocumentProcessor()
    processor.set_chunk_size(500)
    doc = {'content': {'body': 'test ' * 1000}}
    result = processor.process(doc)
    assert result['content']['chunks']
    assert all(len(chunk) <= 500 for chunk in result['content']['chunks'])