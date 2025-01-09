"""Tests for circular reference detection in document relationships.

This module contains tests that verify the handling of circular references
between documents, including self-references and cyclic dependencies.
"""
from copy import deepcopy
from typing import Any, Dict, List
from uuid import uuid4
import pytest
from src.connectors.direct_documentation_indexing.source_tracking import SourceTracker
from src.indexing.schema import SchemaValidator

def create_document_with_id(doc_id: str) -> Dict[str, Any]:
    """Create a test document with a specific ID."""
    return {'id': doc_id, 'content_body': f'Test document {doc_id}', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'parent_id': None, 'chunk_ids': [], 'embedding': [0.1] * 384}

def test_direct_circular_reference():
    """Test detection of direct circular references where A -> A."""
    doc_id = str(uuid4())
    doc = create_document_with_id(doc_id)
    doc['parent_id'] = doc_id
    with pytest.raises(ValueError, match='circular.*reference'):
        SchemaValidator.validate_object(doc)

def test_indirect_circular_reference():
    """Test detection of indirect circular references where A -> B -> A."""
    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())
    doc_a = create_document_with_id(doc_a_id)
    doc_b = create_document_with_id(doc_b_id)
    doc_a['parent_id'] = doc_b_id
    doc_b['parent_id'] = doc_a_id
    with pytest.raises(ValueError, match='circular.*reference'):
        SchemaValidator.validate_object(doc_a)
        SchemaValidator.validate_object(doc_b)

def test_complex_circular_reference():
    """Test detection of complex circular references where A -> B -> C -> A."""
    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())
    doc_c_id = str(uuid4())
    doc_a = create_document_with_id(doc_a_id)
    doc_b = create_document_with_id(doc_b_id)
    doc_c = create_document_with_id(doc_c_id)
    doc_a['parent_id'] = doc_b_id
    doc_b['parent_id'] = doc_c_id
    doc_c['parent_id'] = doc_a_id
    with pytest.raises(ValueError, match='circular.*reference'):
        SchemaValidator.validate_object(doc_a)
        SchemaValidator.validate_object(doc_b)
        SchemaValidator.validate_object(doc_c)

def test_self_reference_in_chunks():
    """Test detection of self-references in chunk_ids."""
    doc_id = str(uuid4())
    doc = create_document_with_id(doc_id)
    doc['chunk_ids'] = [str(uuid4()), doc_id, str(uuid4())]
    with pytest.raises(ValueError, match='self-reference'):
        SchemaValidator.validate_object(doc)

def test_circular_chunk_reference():
    """Test detection of circular references through chunk relationships."""
    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())
    doc_a = create_document_with_id(doc_a_id)
    doc_b = create_document_with_id(doc_b_id)
    doc_a['chunk_ids'] = [doc_b_id]
    doc_b['chunk_ids'] = [doc_a_id]
    with pytest.raises(ValueError, match='circular.*reference'):
        SchemaValidator.validate_object(doc_a)
        SchemaValidator.validate_object(doc_b)

def test_mixed_circular_reference():
    """Test detection of circular references mixing parent and chunk relationships."""
    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())
    doc_a = create_document_with_id(doc_a_id)
    doc_b = create_document_with_id(doc_b_id)
    doc_a['parent_id'] = doc_b_id
    doc_b['chunk_ids'] = [doc_a_id]
    with pytest.raises(ValueError, match='circular.*reference'):
        SchemaValidator.validate_object(doc_a)
        SchemaValidator.validate_object(doc_b)

def test_valid_complex_relationships():
    """Test that valid complex relationships are accepted."""
    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())
    doc_c_id = str(uuid4())
    doc_a = create_document_with_id(doc_a_id)
    doc_b = create_document_with_id(doc_b_id)
    doc_c = create_document_with_id(doc_c_id)
    doc_a['parent_id'] = doc_b_id
    doc_b['parent_id'] = doc_c_id
    SchemaValidator.validate_object(doc_a)
    SchemaValidator.validate_object(doc_b)
    SchemaValidator.validate_object(doc_c)