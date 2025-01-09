"""Advanced text chunking with paragraph detection and special case handling.

This module implements Weaviate's recommended chunking strategy using paragraphs as the base unit.
The AdvancedChunker class provides intelligent text segmentation with the following features:

1. Paragraph Detection:
   - Natural language paragraph boundaries
   - Semantic coherence preservation
   - Variable chunk sizes (25-100 words as per Weaviate docs)

2. Special Case Handling:
   - Code blocks (indented, fenced with backticks, quotes)
   - Lists (-, *, +, 1., bullet)
   - Tables (|, +-, +=)

3. Size Management:
   - Minimum and maximum chunk sizes
   - Chunk merging for undersized segments
   - Chunk splitting for oversized segments
   - Configurable overlap between chunks
"""

from typing import List, Tuple


class AdvancedChunker:
    """Advanced text chunking with paragraph detection and special case handling.

    This class implements Weaviate's recommended chunking strategy, using paragraphs
    as the base unit while preserving special content structures like code blocks,
    lists, and tables. It maintains semantic coherence by respecting natural text
    boundaries and handles edge cases through intelligent merging and splitting.

    Attributes:
        min_chunk_size: Minimum number of words per chunk (default: 25)
        max_chunk_size: Maximum number of words per chunk (default: 100)
        overlap: Number of words to overlap between chunks (default: 5)
        code_markers: Set of markers that indicate code blocks
        list_markers: Set of markers that indicate list items
        table_markers: Set of markers that indicate table rows
    """

    def __init__(
        self,
        min_chunk_size: int = 25,  # words
        max_chunk_size: int = 100,  # words
        overlap: int = 5,  # words
    ):
        """Initialize the AdvancedChunker with size constraints.

        Args:
            min_chunk_size: Minimum words per chunk (Weaviate recommended: 25)
            max_chunk_size: Maximum words per chunk (Weaviate recommended: 100)
            overlap: Number of words to overlap between chunks
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

        # Special case markers
        self.code_markers = {"```", "'''", '"""', "    ", "\t"}  # Code blocks  # Indented code
        self.list_markers = {"-", "*", "+", "1.", "•"}
        self.table_markers = {"|", "+-", "+="}

    def _is_code_block(self, text: str) -> bool:
        """Detect if text is part of a code block."""
        return any(text.lstrip().startswith(marker) for marker in self.code_markers)

    def _is_list_item(self, text: str) -> bool:
        """Detect if text is a list item."""
        return any(text.lstrip().startswith(marker) for marker in self.list_markers)

    def _is_table_row(self, text: str) -> bool:
        """Detect if text is part of a table."""
        return any(text.lstrip().startswith(marker) for marker in self.table_markers)

    def _get_special_case_block(self, lines: List[str], start: int) -> Tuple[int, List[str]]:
        """Extract a special case block (code, list, table) starting from given index."""
        block = []
        i = start

        # Determine block type from first line
        first_line = lines[start].lstrip()
        is_code = self._is_code_block(first_line)
        is_list = self._is_list_item(first_line)
        is_table = self._is_table_row(first_line)

        while i < len(lines):
            line = lines[i].rstrip()
            if not line:  # Empty line marks end of block
                break

            if is_code and self._is_code_block(line):
                block.append(line)
            elif is_list and self._is_list_item(line):
                block.append(line)
            elif is_table and self._is_table_row(line):
                block.append(line)
            elif not any([is_code, is_list, is_table]):  # Regular paragraph
                block.append(line)
            else:
                break
            i += 1

        return i, block

    def _split_oversized_chunk(self, text: str) -> List[str]:
        """Split a chunk that exceeds max_chunk_size into smaller chunks."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.max_chunk_size - self.overlap):
            chunk = " ".join(words[i : i + self.max_chunk_size])
            if len(chunk.split()) >= self.min_chunk_size:
                chunks.append(chunk)

        return chunks

    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """Merge chunks smaller than min_chunk_size with neighbors."""
        if not chunks:
            return chunks

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            combined = f"{current} {next_chunk}"
            if len(combined.split()) <= self.max_chunk_size:
                current = combined
            else:
                if len(current.split()) >= self.min_chunk_size:
                    merged.append(current)
                current = next_chunk

        if current and len(current.split()) >= self.min_chunk_size:
            merged.append(current)

        return merged

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks based on paragraphs and special cases.

        Args:
            text: Text to split into chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Split into lines while preserving empty lines
        lines = text.splitlines()
        chunks = []
        current_para = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # Handle special cases
            if self._is_code_block(line) or self._is_list_item(line) or self._is_table_row(line):
                # First, add any accumulated paragraph
                if current_para:
                    para_text = " ".join(current_para)
                    chunks.extend(self._split_oversized_chunk(para_text))
                    current_para = []

                # Then handle the special case block
                next_i, block = self._get_special_case_block(lines, i)
                if block:
                    block_text = "\n".join(block)
                    chunks.extend(self._split_oversized_chunk(block_text))
                i = next_i
                continue

            # Handle regular paragraphs
            if not line and current_para:  # Empty line marks paragraph end
                para_text = " ".join(current_para)
                chunks.extend(self._split_oversized_chunk(para_text))
                current_para = []
            elif line:  # Non-empty line
                current_para.append(line)

            i += 1

        # Add final paragraph if exists
        if current_para:
            para_text = " ".join(current_para)
            chunks.extend(self._split_oversized_chunk(para_text))

        # Merge any small chunks
        return self._merge_small_chunks(chunks)
