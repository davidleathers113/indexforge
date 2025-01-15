"""Unit tests for the paragraph-based chunking system."""
import pytest

from src.utils.chunking import ChunkingConfig, ParagraphChunker


@pytest.fixture
def default_config():
    """Default chunking configuration for tests."""
    return ChunkingConfig(use_advanced_chunking=True, min_chunk_size=25, max_chunk_size=100, chunk_overlap=5)

@pytest.fixture
def chunker(default_config):
    """ParagraphChunker instance with default config."""
    return ParagraphChunker(default_config)

def test_empty_text_returns_empty_list(chunker):
    """Test that empty text input returns an empty list."""
    assert chunker.chunk_text('') == []

def test_single_short_paragraph_remains_intact(chunker):
    """Test that a single short paragraph is not split."""
    text = 'This is a short paragraph that should remain as one chunk.'
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_code_block_preserved(chunker):
    """Test that code blocks are kept intact."""
    code_block = "```python\ndef hello():\n    print('world')\n```"
    chunks = chunker.chunk_text(code_block)
    assert len(chunks) == 1
    assert chunks[0] == code_block

def test_inline_code_preserved(chunker):
    """Test that inline code is preserved."""
    text = 'Use the `print()` function to output text.'
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_list_items_grouped(chunker):
    """Test that list items are kept together when possible."""
    list_text = '- Item 1\n- Item 2\n- Item 3'
    chunks = chunker.chunk_text(list_text)
    assert len(chunks) == 1
    assert chunks[0] == list_text

def test_numbered_list_items_grouped(chunker):
    """Test that numbered list items are kept together."""
    list_text = '1. First item\n2. Second item\n3. Third item'
    chunks = chunker.chunk_text(list_text)
    assert len(chunks) == 1
    assert chunks[0] == list_text

def test_table_preserved(chunker):
    """Test that markdown tables are kept intact."""
    table = '| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |'
    chunks = chunker.chunk_text(table)
    assert len(chunks) == 1
    assert chunks[0] == table

def test_multiple_paragraphs_split(chunker):
    """Test that multiple paragraphs are split appropriately."""
    text = 'First paragraph.\n\nSecond paragraph.\n\nThird paragraph.'
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 3
    assert 'First paragraph' in chunks[0]
    assert 'Second paragraph' in chunks[1]
    assert 'Third paragraph' in chunks[2]

def test_oversized_paragraph_split_at_sentences(chunker):
    """Test that large paragraphs are split at sentence boundaries."""
    long_text = '. '.join(['This is sentence ' + str(i) for i in range(10)])
    chunks = chunker.chunk_text(long_text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert not chunk.startswith(' ')
        assert chunk.endswith('.')

def test_respects_min_chunk_size(chunker):
    """Test that chunks respect the minimum size configuration."""
    text = 'Short. Very short. Tiny bits. Small pieces.'
    chunks = chunker.chunk_text(text)
    for chunk in chunks:
        tokens = chunker.config.count_tokens(chunk)
        assert tokens >= chunker.config.min_chunk_size

def test_respects_max_chunk_size(chunker):
    """Test that chunks respect the maximum size configuration."""
    long_text = ' '.join(['word' for _ in range(200)])
    chunks = chunker.chunk_text(long_text)
    for chunk in chunks:
        tokens = chunker.config.count_tokens(chunk)
        assert tokens <= chunker.config.max_chunk_size

def test_mixed_content_handling(chunker):
    """Test handling of mixed content types (paragraphs, code, lists)."""
    mixed_text = '\nFirst paragraph.\n\n```python\ndef test():\n    pass\n```\n\n- List item 1\n- List item 2\n\nSecond paragraph.\n'
    chunks = chunker.chunk_text(mixed_text.strip())
    assert len(chunks) > 1
    code_chunk = next((chunk for chunk in chunks if '```python' in chunk))
    assert 'def test():' in code_chunk
    list_chunk = next((chunk for chunk in chunks if '- List item 1' in chunk))
    assert '- List item 2' in list_chunk

def test_nested_list_handling(chunker):
    """Test handling of nested lists with multiple levels."""
    nested_list = '\n- Level 1 Item\n  - Level 2 Item A\n    - Level 3 Item X\n    - Level 3 Item Y\n  - Level 2 Item B\n- Another Level 1 Item\n    '
    chunks = chunker.chunk_text(nested_list.strip())
    assert len(chunks) == 1
    assert 'Level 3 Item' in chunks[0]
    assert chunks[0].count('Level 2') == 2

def test_mixed_nested_content(chunker):
    """Test handling of intermixed code blocks within lists."""
    mixed_nested = '\n- First item\n  ```python\n  def nested_code():\n      return True\n  ```\n- Second item\n  - Nested item with `inline code`\n    ```python\n    more_code()\n    ```\n    '
    chunks = chunker.chunk_text(mixed_nested.strip())
    code_chunk = next((chunk for chunk in chunks if 'def nested_code()' in chunk))
    assert 'First item' in code_chunk
    assert '```python' in code_chunk

def test_malformed_markdown_handling(chunker):
    """Test handling of malformed markdown content."""
    malformed_text = '\nUnclosed code block:\n```python\ndef broken():\n    print("no closing backticks")\n\nMismatched table cells:\n| Header 1 | Header 2 |\n|----------|\n| Cell 1   | Cell 2   | Extra Cell |\n\nUnbalanced inline code: `unclosed code\n    '
    chunks = chunker.chunk_text(malformed_text.strip())
    assert len(chunks) > 0
    assert 'def broken()' in ''.join(chunks)

def test_extremely_long_paragraph(chunker):
    """Test handling of extremely long paragraphs without natural breaks."""
    long_words = ['word' + str(i) for i in range(1000)]
    long_text = ' '.join(long_words)
    chunks = chunker.chunk_text(long_text)
    assert len(chunks) > 1
    for chunk in chunks:
        tokens = chunker.config.count_tokens(chunk)
        assert tokens <= chunker.config.max_chunk_size

def test_special_characters_handling(chunker):
    """Test handling of text with special characters and Unicode."""
    special_text = '\nFirst paragraph with emoji 🚀 and Unicode characters ñ, é, 漢字.\n\n```python\n# Code with special chars: →, ←, ≠\nprint("Hello, 世界!")\n```\n\n- List item with symbols: ♠, ♥, ♦, ♣\n- Mathematical notation: ∑(x²) = ∞\n    '
    chunks = chunker.chunk_text(special_text.strip())
    assert '🚀' in ''.join(chunks)
    assert '漢字' in ''.join(chunks)
    assert '∑(x²)' in ''.join(chunks)

def test_zero_width_spaces_and_control_chars(chunker):
    """Test handling of invisible characters and control characters."""
    control_text = 'Hidden\u200bzero\u200bwidth\u200bspaces.\n\x00\x01Control\x02chars.'
    chunks = chunker.chunk_text(control_text)
    assert len(chunks) > 0
    assert 'Hidden' in chunks[0]
    assert 'Control' in ''.join(chunks)

def test_overlapping_special_blocks(chunker):
    """Test handling of potentially overlapping special block markers."""
    overlapping_text = '\nHere\'s a list with a code block that contains a table:\n- Item 1\n  ```python\n  # | Col1 | Col2 |\n  # |------|------|\n  # | A    | B    |\n  print("table in code")\n  ```\n- Item 2 with `inline | pipe | chars`\n    '
    chunks = chunker.chunk_text(overlapping_text.strip())
    code_chunk = next((chunk for chunk in chunks if '```python' in chunk))
    assert 'print(' in code_chunk
    assert 'Item 1' in code_chunk

def test_empty_special_blocks(chunker):
    """Test handling of empty special blocks."""
    empty_blocks = '\nEmpty code block:\n```\n\n```\n\nEmpty table:\n| |\n|-|\n| |\n\nEmpty list:\n-\n-\n    '
    chunks = chunker.chunk_text(empty_blocks.strip())
    assert len(chunks) > 0
    assert '```\n\n```' in ''.join(chunks)
    assert 'Empty code block' in chunks[0]

def test_maximum_nesting_depth(chunker):
    """Test handling of deeply nested structures."""
    deep_nest = '  ' * 10 + '- Deeply nested item\n' + '  ' * 20 + '- Even deeper'
    chunks = chunker.chunk_text(deep_nest)
    assert len(chunks) > 0
    assert 'Deeply nested item' in chunks[0]
    assert 'Even deeper' in chunks[0]