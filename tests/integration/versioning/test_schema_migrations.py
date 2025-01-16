"""Tests for schema migration scenarios in schema integration.

This module contains tests that verify the migration process between
different schema versions, including rollback scenarios and partial updates.
"""
from typing import Any

import pytest

from src.indexing.schema import SchemaMigrator


def create_v1_document() -> dict[str, Any]:
    """Create a document using schema version 1 format."""
    return {'content': 'Legacy content without body/summary split', 'timestamp': '2024-01-20T12:00:00Z', 'version': 1, 'parent': None, 'chunks': [], 'vector': [0.1] * 384}


def test_migrate_v1_to_latest(base_schema):
    """Test migration from version 1 to latest schema version."""
    old_doc = create_v1_document()
    migrated_doc = SchemaMigrator.migrate_to_latest(old_doc)
    assert 'content_body' in migrated_doc
    assert 'timestamp_utc' in migrated_doc
    assert 'schema_version' in migrated_doc
    assert 'parent_id' in migrated_doc
    assert 'chunk_ids' in migrated_doc
    assert 'embedding' in migrated_doc
    assert isinstance(migrated_doc['content_body'], str)
    assert 'content_summary' in migrated_doc
    assert migrated_doc['schema_version'] == base_schema['version']


def test_migrate_batch_documents(base_schema):
    """Test migration of multiple documents in batch."""
    old_docs = [create_v1_document() for _ in range(5)]
    old_docs[1]['extra_field'] = 'should be preserved'
    old_docs[2]['vector'] = None
    old_docs[3]['chunks'] = ['chunk1', 'chunk2']
    migrated_docs = SchemaMigrator.migrate_batch(old_docs)
    assert len(migrated_docs) == len(old_docs)
    for doc in migrated_docs:
        assert doc['schema_version'] == base_schema['version']
    assert 'extra_field' in migrated_docs[1]
    assert len(migrated_docs[3]['chunk_ids']) == 2


def test_migration_rollback(base_schema):
    """Test rollback scenario when migration fails."""
    old_docs = [create_v1_document(), {'invalid': 'document'}, create_v1_document()]
    with pytest.raises(ValueError):
        SchemaMigrator.migrate_batch(old_docs)
    assert 'content' in old_docs[0]
    assert 'invalid' in old_docs[1]
    assert 'content' in old_docs[2]


def test_partial_schema_update(base_schema):
    """Test migration where only some fields need updating."""
    doc = {'content_body': 'Already in new format', 'timestamp': '2024-01-20T12:00:00Z', 'schema_version': base_schema['version'] - 1, 'parent_id': None, 'chunk_ids': [], 'embedding': [0.1] * 384}
    migrated_doc = SchemaMigrator.migrate_to_latest(doc)
    assert 'timestamp_utc' in migrated_doc
    assert migrated_doc['schema_version'] == base_schema['version']
    assert migrated_doc['content_body'] == doc['content_body']


def test_migrate_with_custom_fields(base_schema):
    """Test migration with custom metadata fields."""
    old_doc = create_v1_document()
    old_doc['metadata'] = {'author': 'John Doe', 'legacy_field': 'old value', 'tags': ['tag1', 'tag2']}
    field_mappings = {'legacy_field': 'new_field', 'tags': 'categories'}
    migrated_doc = SchemaMigrator.migrate_to_latest(old_doc, custom_field_mappings=field_mappings)
    assert 'new_field' in migrated_doc['metadata']
    assert 'categories' in migrated_doc['metadata']
    assert 'legacy_field' not in migrated_doc['metadata']
    assert migrated_doc['metadata']['author'] == 'John Doe'