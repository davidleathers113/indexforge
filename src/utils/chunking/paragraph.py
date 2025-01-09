"""Paragraph-based text chunking for Weaviate integration.

This module provides intelligent paragraph-based text chunking that maintains
semantic coherence and handles special cases like lists, code blocks, and tables.

The chunking strategy follows these principles:
1. Respect natural paragraph boundaries
2. Handle special content types (lists, code blocks, tables)
3. Maintain semantic coherence
4. Support variable chunk sizes within configured bounds
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

from .base import ChunkingConfig


@dataclass
class ContentBlock:
    """Represents a block of content with its type and metadata."""

    text: str
    block_type: str  # 'paragraph', 'list', 'code', 'table'
    token_count: int
    metadata: dict


class ParagraphChunker:
    """Intelligent paragraph-based text chunking."""

    # Regex patterns for special content detection
    CODE_BLOCK_PATTERN = r"```[\s\S]*?```|`[^`]+`"
    LIST_ITEM_PATTERN = r"^\s*[-*+]\s+|^\s*\d+\.\s+"
    TABLE_PATTERN = r"\|[^|]+\|[^|]+\|"

    def __init__(self, config: ChunkingConfig):
        """Initialize with chunking configuration."""
        if not config.use_advanced_chunking:
            config.use_advanced_chunking = True
        self.config = config

    def chunk_text(self, text: str) -> List[str]:
        """Main entry point for paragraph-based text chunking."""
        # 1. Split into content blocks while preserving special blocks
        blocks = self._split_into_blocks(text)

        # 2. Combine blocks into coherent chunks
        return self._combine_blocks(blocks)

    def _split_into_blocks(self, text: str) -> List[ContentBlock]:
        """Split text into content blocks while preserving special content."""
        blocks = []
        current_pos = 0

        # First, extract and protect special blocks
        special_blocks = self._extract_special_blocks(text)

        # Process text between special blocks
        for special_start, special_end, block_type in special_blocks:
            # Process text before special block
            if current_pos < special_start:
                normal_text = text[current_pos:special_start]
                blocks.extend(self._process_normal_text(normal_text))

            # Add the special block
            special_text = text[special_start:special_end]
            blocks.append(
                ContentBlock(
                    text=special_text,
                    block_type=block_type,
                    token_count=self.config.count_tokens(special_text),
                    metadata={"original": True},
                )
            )
            current_pos = special_end

        # Process remaining text
        if current_pos < len(text):
            blocks.extend(self._process_normal_text(text[current_pos:]))

        return blocks

    def _extract_special_blocks(self, text: str) -> List[Tuple[int, int, str]]:
        """Extract positions and types of special content blocks."""
        special_blocks = []

        # Find code blocks
        for match in re.finditer(self.CODE_BLOCK_PATTERN, text, re.MULTILINE):
            special_blocks.append((match.start(), match.end(), "code"))

        # Find table blocks
        for match in re.finditer(self.TABLE_PATTERN, text, re.MULTILINE):
            if not any(start <= match.start() <= end for start, end, _ in special_blocks):
                special_blocks.append((match.start(), match.end(), "table"))

        # Sort blocks by start position
        return sorted(special_blocks, key=lambda x: x[0])

    def _process_normal_text(self, text: str) -> List[ContentBlock]:
        """Process normal text into paragraph blocks."""
        blocks = []

        # Split into paragraphs
        paragraphs = re.split(r"\n\s*\n", text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if it's a list
            if re.match(self.LIST_ITEM_PATTERN, para, re.MULTILINE):
                blocks.append(
                    ContentBlock(
                        text=para,
                        block_type="list",
                        token_count=self.config.count_tokens(para),
                        metadata={"list_items": para.count("\n") + 1},
                    )
                )
            else:
                blocks.append(
                    ContentBlock(
                        text=para,
                        block_type="paragraph",
                        token_count=self.config.count_tokens(para),
                        metadata={},
                    )
                )

        return blocks

    def _combine_blocks(self, blocks: List[ContentBlock]) -> List[str]:
        """Combine blocks into coherent chunks respecting size constraints."""
        chunks = []
        current_chunk = []
        current_tokens = 0

        for block in blocks:
            # If block is too large, split it
            if block.token_count > self.config.max_chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split large block
                split_chunks = self._split_large_block(block)
                chunks.extend(split_chunks)
                continue

            # If adding block would exceed max_chunk_size, start new chunk
            if current_tokens + block.token_count > self.config.max_chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            # Add block to current chunk
            current_chunk.append(block.text)
            current_tokens += block.token_count

            # If current chunk is within size bounds, consider it complete
            if self.config.min_chunk_size <= current_tokens <= self.config.max_chunk_size:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

        # Add any remaining content
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_large_block(self, block: ContentBlock) -> List[str]:
        """Split a large block into smaller chunks."""
        if block.block_type in ("code", "table"):
            # Don't split code or table blocks, return as is
            return [block.text]

        # For paragraphs and lists, use sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", block.text)
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.config.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.config.max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
