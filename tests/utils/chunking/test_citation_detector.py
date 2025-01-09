"""Tests for citation detection and classification.

These tests verify the functionality of citation detection, including
different citation types and reference creation.
"""
from uuid import uuid4
import pytest
from src.utils.chunking.citation_detector import CitationDetector, CitationType
from src.utils.chunking.references import ReferenceManager, ReferenceType

@pytest.fixture
def ref_manager():
    """Create a reference manager with test chunks."""
    manager = ReferenceManager()
    manager.add_chunk('This is a source text that contains "a direct quote" from another section.', uuid4())
    manager.add_chunk('This is the target text containing a direct quote and more content.', uuid4())
    manager.add_chunk('As described in Section 3.2, the process involves multiple steps.', uuid4())
    manager.add_chunk('Section 3.2: Process Steps', uuid4())
    manager.add_chunk('For more details, see https://example.com/docs', uuid4())
    manager.add_chunk('The documentation at https://example.com/docs explains further.', uuid4())
    return manager

@pytest.fixture
def citation_detector(ref_manager):
    """Create a citation detector with the test reference manager."""
    return CitationDetector(ref_manager)

def test_detect_direct_quotes(citation_detector):
    """Test detection of direct quotes."""
    chunk_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if '"a direct quote"' in chunk.content))
    citations = citation_detector.detect_citations(chunk_id)
    quote_citations = [c for c in citations if c.citation_type == CitationType.DIRECT_QUOTE]
    assert len(quote_citations) == 1
    assert quote_citations[0].text == 'a direct quote'
    assert quote_citations[0].source_chunk_id == chunk_id

def test_detect_inline_references(citation_detector):
    """Test detection of inline section references."""
    chunk_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if 'As described in Section 3.2' in chunk.content))
    citations = citation_detector.detect_citations(chunk_id)
    inline_citations = [c for c in citations if c.citation_type == CitationType.INLINE_REFERENCE]
    assert len(inline_citations) == 1
    assert 'Section 3.2' in inline_citations[0].text
    assert inline_citations[0].source_chunk_id == chunk_id

def test_detect_urls(citation_detector):
    """Test detection of URL references."""
    chunk_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if 'https://example.com/docs' in chunk.content))
    citations = citation_detector.detect_citations(chunk_id)
    url_citations = [c for c in citations if c.citation_type == CitationType.URL]
    assert len(url_citations) == 1
    assert url_citations[0].text == 'https://example.com/docs'
    assert url_citations[0].source_chunk_id == chunk_id

def test_create_citation_references(citation_detector):
    """Test creation of references from citations."""
    source_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if '"a direct quote"' in chunk.content))
    created_refs = citation_detector.create_citation_references(source_id)
    assert len(created_refs) > 0
    for target_id, ref_type, metadata in created_refs:
        refs = citation_detector.ref_manager.get_references(source_id, ReferenceType.CITATION)
        assert target_id in refs
        assert 'citation_type' in metadata
        assert 'cited_text' in metadata
        assert 'position' in metadata

def test_citation_metadata(citation_detector):
    """Test citation metadata is correctly captured."""
    source_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if 'https://example.com/docs' in chunk.content))
    citations = citation_detector.detect_citations(source_id)
    url_citation = next((c for c in citations if c.citation_type == CitationType.URL))
    assert url_citation.metadata is not None
    assert 'full_match' in url_citation.metadata
    assert url_citation.start_pos >= 0
    assert url_citation.end_pos > url_citation.start_pos

def test_bidirectional_citation_references(citation_detector):
    """Test that citation references are created bidirectionally."""
    source_id = next((chunk_id for chunk_id, chunk in citation_detector.ref_manager._chunks.items() if '"a direct quote"' in chunk.content))
    created_refs = citation_detector.create_citation_references(source_id)
    for target_id, _, _ in created_refs:
        forward_refs = citation_detector.ref_manager.get_references(source_id, ReferenceType.CITATION)
        assert target_id in forward_refs
        backward_refs = citation_detector.ref_manager.get_references(target_id, ReferenceType.CITATION)
        assert source_id in backward_refs

def test_multiple_citation_types(citation_detector):
    """Test detection of multiple citation types in the same chunk."""
    content = 'According to Smith (2020), "this is a quote" that explains everything. For more details, see Section 4.2 or visit https://example.com'
    chunk_id = citation_detector.ref_manager.add_chunk(content)
    citations = citation_detector.detect_citations(chunk_id)
    citation_types = {c.citation_type for c in citations}
    assert CitationType.DIRECT_QUOTE in citation_types
    assert CitationType.AUTHOR_YEAR in citation_types
    assert CitationType.INLINE_REFERENCE in citation_types
    assert CitationType.URL in citation_types