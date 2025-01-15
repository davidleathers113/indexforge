"""Integration tests for the chunking system.

These tests verify that the chunking system works correctly as a whole,
including configuration, chunking strategies, and special content handling.
"""
import pytest

from src.utils.chunking import (
    ChunkingConfig,
    ParagraphChunker,
    chunk_text_by_chars,
    chunk_text_by_tokens,
    chunk_text_by_words,
)


def load_test_document(name: str) -> str:
    """Load a test document from the test data directory."""
    import os
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    with open(os.path.join(test_data_dir, name), 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def markdown_document() -> str:
    """A complex markdown document with various content types."""
    return '# Test Document\n\n## Introduction\nThis is a test document that contains various types of content\nthat our chunking system needs to handle properly.\n\n## Code Examples\nHere\'s some Python code:\n```python\ndef hello_world():\n    print("Hello, World!")\n    return True\n```\n\nAnd some inline code: `print("inline")`.\n\n## Lists and Tables\nHere\'s a list:\n- Item 1\n  - Nested item A\n  - Nested item B\n- Item 2\n  - Nested item X\n    - Deep nest 1\n    - Deep nest 2\n\nAnd a table:\n| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n| Cell 3   | Cell 4   |\n\n## Mixed Content\n1. First numbered item with `inline code`\n2. Second item with a table:\n   | A | B |\n   |---|---|\n   | 1 | 2 |\n\n## Conclusion\nThis document tests various markdown features and their interaction.\n'

def test_end_to_end_token_chunking(markdown_document):
    """Test token-based chunking with a complete markdown document."""
    config = ChunkingConfig(chunk_size=100, chunk_overlap=10, model_name='text-embedding-3-small')
    chunks = chunk_text_by_tokens(markdown_document, config)
    assert len(chunks) > 0
    for chunk in chunks:
        tokens = config.count_tokens(chunk)
        assert tokens <= config.chunk_size
    full_text = ''.join(chunks)
    assert '# Test Document' in full_text
    assert '```python' in full_text
    assert 'def hello_world():' in full_text
    assert '| Header 1 |' in full_text

def test_end_to_end_paragraph_chunking(markdown_document):
    """Test paragraph-based chunking with a complete markdown document."""
    config = ChunkingConfig(use_advanced_chunking=True, min_chunk_size=25, max_chunk_size=100)
    chunker = ParagraphChunker(config)
    chunks = chunker.chunk_text(markdown_document)
    assert len(chunks) > 0
    for chunk in chunks:
        tokens = config.count_tokens(chunk)
        assert tokens >= config.min_chunk_size
        assert tokens <= config.max_chunk_size
    code_chunk = next((chunk for chunk in chunks if '```python' in chunk))
    assert 'def hello_world():' in code_chunk
    assert 'print(' in code_chunk
    list_chunk = next((chunk for chunk in chunks if '- Item 1' in chunk))
    assert '- Nested item' in list_chunk
    table_chunk = next((chunk for chunk in chunks if '| Header 1 |' in chunk))
    assert '| Cell 1' in table_chunk

def test_real_world_document_sizes():
    """Test chunking with realistic document sizes."""
    sections = []
    for i in range(100):
        sections.append(f'# Section {i}\n\nThis is paragraph {i} with some content that needs to be processed.\nIt contains multiple sentences to test proper chunking behavior.\n\n```python\ndef function_{i}():\n    return "test"\n```\n\n- List item {i}.1\n- List item {i}.2\n  - Nested item {i}.a\n  - Nested item {i}.b\n\n| Column 1 | Column 2 |\n|----------|----------|\n| Value {i}a | Value {i}b |\n')
    large_doc = '\n\n'.join(sections)
    configs = [ChunkingConfig(chunk_size=512, chunk_overlap=50), ChunkingConfig(chunk_size=1024, chunk_overlap=100), ChunkingConfig(use_advanced_chunking=True, min_chunk_size=50, max_chunk_size=200)]
    for config in configs:
        if config.use_advanced_chunking:
            chunker = ParagraphChunker(config)
            chunks = chunker.chunk_text(large_doc)
        else:
            chunks = chunk_text_by_tokens(large_doc, config)
        assert len(chunks) > 0
        for chunk in chunks:
            if config.use_advanced_chunking:
                tokens = config.count_tokens(chunk)
                assert config.min_chunk_size <= tokens <= config.max_chunk_size
            else:
                assert config.count_tokens(chunk) <= config.chunk_size

def test_cross_chunking_strategy_comparison(markdown_document):
    """Compare different chunking strategies on the same document."""
    token_config = ChunkingConfig(chunk_size=100, chunk_overlap=10)
    token_chunks = chunk_text_by_tokens(markdown_document, token_config)
    char_chunks = chunk_text_by_chars(markdown_document, chunk_size=500, overlap=50)
    word_chunks = chunk_text_by_words(markdown_document, chunk_size=50, overlap=5)
    para_config = ChunkingConfig(use_advanced_chunking=True, min_chunk_size=25, max_chunk_size=100)
    para_chunker = ParagraphChunker(para_config)
    para_chunks = para_chunker.chunk_text(markdown_document)
    strategies = {'token': token_chunks, 'char': char_chunks, 'word': word_chunks, 'para': para_chunks}
    for strategy, chunks in strategies.items():
        full_text = ''.join(chunks)
        assert '# Test Document' in full_text, f'{strategy} chunking lost headers'
        assert '```python' in full_text, f'{strategy} chunking lost code blocks'
        assert 'def hello_world():' in full_text, f'{strategy} chunking lost code content'
        assert '| Header 1 |' in full_text, f'{strategy} chunking lost tables'
        assert '- Item 1' in full_text, f'{strategy} chunking lost lists'

def test_error_handling_and_recovery():
    """Test error handling and recovery in the chunking pipeline."""
    problematic_doc = '\n# Valid Section\n\n```python\nunclosed code block\n\n| Invalid | Table |\n| Missing | Cells |\n| Extra | Cells | Here |\n\n- Valid list item\n-- Invalid list marker\n- Valid item again\n'
    config = ChunkingConfig(use_advanced_chunking=True)
    chunker = ParagraphChunker(config)
    chunks = chunker.chunk_text(problematic_doc)
    full_text = ''.join(chunks)
    assert '# Valid Section' in full_text
    assert '- Valid list item' in full_text
    assert '- Valid item again' in full_text

def test_unicode_and_special_content_handling():
    """Test handling of Unicode and special content across chunking strategies."""
    special_doc = '\n# Unicode Test 🚀\n\n## Emojis and Symbols\nText with emojis 🌟 and symbols ©®™\n\n## International Text\nChinese: 你好世界\nJapanese: こんにちは世界\nKorean: 안녕하세요 세계\nArabic: مرحبا بالعالم\nRussian: Привет, мир\n\n## Special Characters\nMath: ∑(x²) = ∞\nQuotes: "Smart quotes" and \'apostrophes\'\nDashes: em—dash and en–dash\n'
    configs = [ChunkingConfig(chunk_size=100, chunk_overlap=10), ChunkingConfig(use_advanced_chunking=True)]
    for config in configs:
        if config.use_advanced_chunking:
            chunker = ParagraphChunker(config)
            chunks = chunker.chunk_text(special_doc)
        else:
            chunks = chunk_text_by_tokens(special_doc, config)
        full_text = ''.join(chunks)
        assert '🚀' in full_text, 'Emojis not preserved'
        assert '你好世界' in full_text, 'Chinese characters not preserved'
        assert 'こんにちは世界' in full_text, 'Japanese characters not preserved'
        assert '∑(x²) = ∞' in full_text, 'Mathematical symbols not preserved'
        assert 'em—dash' in full_text, 'Special punctuation not preserved'