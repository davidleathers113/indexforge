"""Citation detection and classification for text chunks.

This module provides functionality for identifying and classifying citations
within and across chunks, supporting both explicit and implicit citations.
"""

from dataclasses import dataclass
from enum import Enum
import re
from uuid import UUID

from .references import ReferenceManager, ReferenceType


class CitationType(Enum):
    """Types of citations that can be detected."""

    DIRECT_QUOTE = "direct_quote"  # Exact text enclosed in quotes
    INLINE_REFERENCE = "inline_reference"  # Explicit reference to another section
    NUMBERED_REFERENCE = "numbered_reference"  # [1], [2], etc.
    AUTHOR_YEAR = "author_year"  # (Author, Year) style citations
    FOOTNOTE = "footnote"  # Footnote or endnote reference
    URL = "url"  # URL or hyperlink reference


@dataclass
class Citation:
    """Represents a detected citation within a chunk."""

    source_chunk_id: UUID
    citation_type: CitationType
    text: str  # The cited text or reference
    start_pos: int  # Start position in chunk
    end_pos: int  # End position in chunk
    metadata: dict = None  # Additional citation metadata


class CitationDetector:
    """Detects and classifies citations within text chunks."""

    def __init__(self, ref_manager: ReferenceManager):
        """Initialize the citation detector.

        Args:
            ref_manager: Reference manager to use for creating citation references
        """
        self.ref_manager = ref_manager
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize regex patterns for citation detection."""
        self.patterns = {
            CitationType.DIRECT_QUOTE: re.compile(
                r'"([^"]+)"|\u201C([^\u201D]+)\u201D'
            ),  # Smart and regular quotes
            CitationType.INLINE_REFERENCE: re.compile(
                r'(?:see|refer to|as shown in|as described in)\s+(?:section|chapter)?\s*[""]?([^.,"]+)[""]?',
                re.IGNORECASE,
            ),
            CitationType.NUMBERED_REFERENCE: re.compile(r"\[(\d+)\]|\((\d+)\)"),
            CitationType.AUTHOR_YEAR: re.compile(r"\(([^)]+?,\s*\d{4}(?:-\d{4})?)\)"),
            CitationType.FOOTNOTE: re.compile(r"(?:(?<=[^0-9])|^)\[(\d+)\]|\{\^(\d+)\}"),
            CitationType.URL: re.compile(r"https?://\S+|www\.\S+"),
        }

    def detect_citations(self, chunk_id: UUID) -> list[Citation]:
        """Detect all citations within a chunk.

        Args:
            chunk_id: ID of the chunk to analyze

        Returns:
            List of detected citations
        """
        chunk = self.ref_manager._chunks.get(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} does not exist")

        citations = []
        content = chunk.content

        # Detect each type of citation
        for citation_type, pattern in self.patterns.items():
            for match in pattern.finditer(content):
                # Get the matched text and its position
                text = next(group for group in match.groups() if group is not None)
                start_pos = match.start()
                end_pos = match.end()

                citation = Citation(
                    source_chunk_id=chunk_id,
                    citation_type=citation_type,
                    text=text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    metadata={"full_match": match.group(0)},
                )
                citations.append(citation)

        return citations

    def create_citation_references(self, chunk_id: UUID) -> list[tuple[UUID, ReferenceType, dict]]:
        """Create references for detected citations.

        Args:
            chunk_id: ID of the chunk to process

        Returns:
            List of (target_chunk_id, reference_type, metadata) tuples for created references
        """
        citations = self.detect_citations(chunk_id)
        created_refs = []

        for citation in citations:
            # Try to find target chunk for the citation
            target_chunk_id = self._find_citation_target(citation)
            if target_chunk_id:
                metadata = {
                    "citation_type": citation.citation_type.value,
                    "cited_text": citation.text,
                    "position": {"start": citation.start_pos, "end": citation.end_pos},
                }
                if citation.metadata:
                    metadata.update(citation.metadata)

                # Create the reference
                self.ref_manager.add_reference(
                    chunk_id,
                    target_chunk_id,
                    ReferenceType.CITATION,
                    metadata=metadata,
                    bidirectional=True,
                )
                created_refs.append((target_chunk_id, ReferenceType.CITATION, metadata))

        return created_refs

    def _find_citation_target(self, citation: Citation) -> UUID | None:
        """Find the target chunk for a citation.

        Args:
            citation: The citation to find a target for

        Returns:
            UUID of the target chunk if found, None otherwise
        """
        # Different strategies based on citation type
        if citation.citation_type == CitationType.DIRECT_QUOTE:
            return self._find_quote_target(citation.text)
        elif citation.citation_type == CitationType.INLINE_REFERENCE:
            return self._find_section_target(citation.text)
        elif citation.citation_type == CitationType.URL:
            return self._find_url_target(citation.text)

        # For other types, we might need additional context or metadata
        return None

    def _find_quote_target(self, quoted_text: str) -> UUID | None:
        """Find a chunk containing the exact quoted text."""
        for chunk_id, chunk in self.ref_manager._chunks.items():
            if quoted_text in chunk.content:
                return chunk_id
        return None

    def _find_section_target(self, section_reference: str) -> UUID | None:
        """Find a chunk based on section reference."""
        # This could be enhanced with more sophisticated section matching
        normalized_ref = section_reference.lower().strip()
        for chunk_id, chunk in self.ref_manager._chunks.items():
            if normalized_ref in chunk.content.lower():
                return chunk_id
        return None

    def _find_url_target(self, url: str) -> UUID | None:
        """Find a chunk containing the URL reference."""
        for chunk_id, chunk in self.ref_manager._chunks.items():
            if url in chunk.content:
                return chunk_id
        return None
