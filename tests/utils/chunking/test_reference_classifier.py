"""Tests for reference type classification.

These tests verify the functionality of reference classification, including
direct, indirect, and structural references.
"""
import pytest
from src.utils.chunking.citation_detector import CitationType
from src.utils.chunking.reference_classifier import ReferenceCategory, ReferenceClassifier
from src.utils.chunking.references import ReferenceManager, ReferenceType

@pytest.fixture
def ref_manager():
    """Create a reference manager with test references."""
    manager = ReferenceManager()
    chunk1 = manager.add_chunk('Source chunk with a citation')
    chunk2 = manager.add_chunk('Target chunk being cited')
    chunk3 = manager.add_chunk('Similar content about the topic')
    chunk4 = manager.add_chunk('Parent section header')
    chunk5 = manager.add_chunk('Child section content')
    manager.add_reference(chunk1, chunk2, ReferenceType.CITATION, metadata={'citation_type': CitationType.DIRECT_QUOTE.value})
    manager.add_reference(chunk1, chunk3, ReferenceType.SIMILAR, metadata={'similarity_score': 0.85})
    manager.add_reference(chunk4, chunk5, ReferenceType.PARENT)
    return manager

@pytest.fixture
def reference_classifier(ref_manager):
    """Create a reference classifier with the test reference manager."""
    return ReferenceClassifier(ref_manager)

def test_classify_direct_reference(reference_classifier):
    """Test classification of direct references."""
    source_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'citation' in chunk.content.lower()))
    target_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'cited' in chunk.content.lower()))
    classification = reference_classifier.classify_reference(source_id, target_id, ReferenceType.CITATION)
    assert classification.category == ReferenceCategory.DIRECT
    assert classification.confidence > 0.8
    assert 'citation_details' in classification.evidence
    assert classification.metadata['is_explicit_reference']

def test_classify_indirect_reference(reference_classifier):
    """Test classification of indirect references."""
    source_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'citation' in chunk.content.lower()))
    target_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'similar' in chunk.content.lower()))
    classification = reference_classifier.classify_reference(source_id, target_id, ReferenceType.SIMILAR)
    assert classification.category == ReferenceCategory.INDIRECT
    assert 'semantic_details' in classification.evidence
    assert classification.metadata['is_semantic_reference']
    assert classification.evidence['semantic_details']['is_highly_similar']

def test_classify_structural_reference(reference_classifier):
    """Test classification of structural references."""
    parent_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'parent' in chunk.content.lower()))
    child_id = next((chunk_id for chunk_id, chunk in reference_classifier.ref_manager._chunks.items() if 'child' in chunk.content.lower()))
    classification = reference_classifier.classify_reference(parent_id, child_id, ReferenceType.PARENT)
    assert classification.category == ReferenceCategory.STRUCTURAL
    assert 'structural_details' in classification.evidence
    assert classification.metadata['is_structural_reference']
    assert classification.evidence['structural_details']['is_hierarchical']

def test_confidence_calculation(reference_classifier):
    """Test confidence score calculation for different reference types."""
    chunk1 = reference_classifier.ref_manager.add_chunk('Test chunk 1')
    chunk2 = reference_classifier.ref_manager.add_chunk('Test chunk 2')
    reference_classifier.ref_manager.add_reference(chunk1, chunk2, ReferenceType.CITATION, metadata={'citation_type': CitationType.DIRECT_QUOTE.value})
    citation_class = reference_classifier.classify_reference(chunk1, chunk2, ReferenceType.CITATION)
    reference_classifier.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR, metadata={'similarity_score': 0.9})
    similarity_class = reference_classifier.classify_reference(chunk1, chunk2, ReferenceType.SIMILAR)
    reference_classifier.ref_manager.add_reference(chunk1, chunk2, ReferenceType.PARENT)
    structural_class = reference_classifier.classify_reference(chunk1, chunk2, ReferenceType.PARENT)
    assert citation_class.confidence > similarity_class.confidence
    assert similarity_class.confidence > 0.5
    assert structural_class.confidence > 0.5

def test_metadata_enrichment(reference_classifier):
    """Test metadata enrichment for classified references."""
    chunk1 = reference_classifier.ref_manager.add_chunk('Source chunk')
    chunk2 = reference_classifier.ref_manager.add_chunk('Target chunk')
    original_metadata = {'citation_type': CitationType.DIRECT_QUOTE.value, 'custom_field': 'test_value'}
    reference_classifier.ref_manager.add_reference(chunk1, chunk2, ReferenceType.CITATION, metadata=original_metadata)
    reference_classifier.update_reference_metadata(chunk1, chunk2)
    ref = reference_classifier.ref_manager._references[chunk1, chunk2]
    assert 'reference_category' in ref.metadata
    assert 'classification_evidence' in ref.metadata
    assert ref.metadata['custom_field'] == 'test_value'
    assert 'citation_info' in ref.metadata

def test_classify_all_references(reference_classifier):
    """Test bulk classification of all references."""
    chunk1 = reference_classifier.ref_manager.add_chunk('Additional source')
    chunk2 = reference_classifier.ref_manager.add_chunk('Additional target')
    reference_classifier.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR, metadata={'similarity_score': 0.75})
    classifications = reference_classifier.classify_all_references()
    assert len(classifications) == len(reference_classifier.ref_manager._references)
    for classification in classifications.values():
        assert isinstance(classification.category, ReferenceCategory)
        assert 0 <= classification.confidence <= 1
        assert classification.evidence
        assert classification.metadata