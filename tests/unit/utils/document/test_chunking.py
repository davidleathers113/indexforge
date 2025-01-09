"""Tests for document chunking functionality."""
import pytest
from src.utils.document_processing import DocumentProcessor
from tests.fixtures import mock_doc_processor

def test_document_chunking(mock_doc_processor):
    """Test document content chunking."""
    processor = DocumentProcessor()
    processor.set_chunk_size(100)
    content = 'word ' * 50
    doc = {'content': {'body': content}}
    result = processor.process(doc)
    assert 'chunks' in result['content']
    assert len(result['content']['chunks']) > 1
    assert all((len(chunk) <= 100 for chunk in result['content']['chunks']))

def test_chunk_overlap(mock_doc_processor):
    """Test chunk overlap in document processing."""
    processor = DocumentProcessor()
    processor.set_chunk_size(50)
    content = 'unique word ' * 20
    doc = {'content': {'body': content}}
    result = processor.process(doc)
    chunks = result['content']['chunks']
    for i in range(len(chunks) - 1):
        assert chunks[i][-10:] in chunks[i + 1][:20]

def test_small_document_chunking(mock_doc_processor):
    """Test chunking of small documents."""
    processor = DocumentProcessor()
    processor.set_chunk_size(1000)
    doc = {'content': {'body': 'small document'}}
    result = processor.process(doc)
    assert len(result['content']['chunks']) == 1
    assert result['content']['chunks'][0] == 'small document'

def test_custom_chunk_size(mock_doc_processor):
    """Test custom chunk size configuration."""
    processor = DocumentProcessor()
    sizes = [50, 100, 200]
    content = 'test word ' * 50
    for size in sizes:
        processor.set_chunk_size(size)
        result = processor.process({'content': {'body': content}})
        assert all((len(chunk) <= size for chunk in result['content']['chunks']))

def test_empty_chunk_handling(mock_doc_processor):
    """Test handling of potential empty chunks."""
    processor = DocumentProcessor()
    processor.set_chunk_size(10)
    doc = {'content': {'body': 'word    word    word'}}
    result = processor.process(doc)
    assert all((chunk.strip() for chunk in result['content']['chunks']))

def test_chunk_boundary_words(mock_doc_processor):
    """Test that words are not split across chunk boundaries."""
    processor = DocumentProcessor()
    processor.set_chunk_size(10)
    doc = {'content': {'body': 'word1 word2 word3 word4'}}
    result = processor.process(doc)
    for chunk in result['content']['chunks']:
        words = chunk.split()
        assert all((len(word) > 0 for word in words))
        assert not any((word.startswith(' ') or word.endswith(' ') for word in words))