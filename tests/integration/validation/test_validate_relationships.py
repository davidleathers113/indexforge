"""Tests for validating document relationships in schema integration.

This module contains tests that verify the validation of parent-child
relationships and document references when integrating the Core Schema
System with Document Processing Schema.
"""
from copy import deepcopy
from uuid import uuid4
import pytest
from src.indexing.schema import SchemaValidator

def test_parent_id_format(valid_document):
    """Test that parent_id must be None or a valid string ID."""
    doc = deepcopy(valid_document)
    doc['parent_id'] = str(uuid4())
    SchemaValidator.validate_object(doc)
    doc['parent_id'] = None
    SchemaValidator.validate_object(doc)
    doc['parent_id'] = 123
    with pytest.raises(TypeError, match='parent_id.*string'):
        SchemaValidator.validate_object(doc)

def test_chunk_ids_format(valid_document):
    """Test that chunk_ids must be a list of valid string IDs."""
    doc = deepcopy(valid_document)
    doc['chunk_ids'] = [str(uuid4()) for _ in range(3)]
    SchemaValidator.validate_object(doc)
    doc['chunk_ids'] = []
    SchemaValidator.validate_object(doc)
    doc['chunk_ids'] = 'not_a_list'
    with pytest.raises(TypeError, match='chunk_ids.*list'):
        SchemaValidator.validate_object(doc)
    doc['chunk_ids'] = [str(uuid4()), 123, str(uuid4())]
    with pytest.raises(TypeError, match='chunk_ids.*string'):
        SchemaValidator.validate_object(doc)

def test_self_reference_prevention(valid_document):
    """Test that a document cannot reference itself as parent or chunk."""
    doc = deepcopy(valid_document)
    doc_id = str(uuid4())
    doc['parent_id'] = doc_id
    with pytest.raises(ValueError, match='self-reference'):
        SchemaValidator.validate_object(doc, doc_id=doc_id)
    doc['parent_id'] = None
    doc['chunk_ids'] = [str(uuid4()), doc_id, str(uuid4())]
    with pytest.raises(ValueError, match='self-reference'):
        SchemaValidator.validate_object(doc, doc_id=doc_id)

def test_duplicate_chunk_prevention(valid_document):
    """Test that chunk_ids cannot contain duplicates."""
    doc = deepcopy(valid_document)
    chunk_id = str(uuid4())
    doc['chunk_ids'] = [str(uuid4()), chunk_id, chunk_id]
    with pytest.raises(ValueError, match='duplicate.*chunk'):
        SchemaValidator.validate_object(doc)