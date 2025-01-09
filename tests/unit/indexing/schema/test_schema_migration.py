"""Tests for schema migration operations."""
from unittest.mock import patch
import pytest
from src.indexing.schema.schema_migrator import SchemaMigrator
from tests.fixtures import mock_schema_validator, mock_weaviate_client

def test_migrator_deletes_old_schema_when_version_mismatch(mock_weaviate_client, mock_schema_validator):
    """Test that migrator deletes old schema when version doesn't match."""
    migrator = SchemaMigrator(mock_weaviate_client, 'Document', mock_schema_validator)
    mock_schema_validator.check_schema_version.return_value = False
    migrator._migrate_schema()
    mock_weaviate_client.schema.delete_class.assert_called_once_with('Document')

def test_migrator_creates_new_schema_after_deletion(mock_weaviate_client, mock_schema_validator):
    """Test that migrator creates new schema after deleting old one."""
    migrator = SchemaMigrator(mock_weaviate_client, 'Document', mock_schema_validator)
    mock_schema_validator.validate_schema.return_value = True
    mock_schema = {'class': 'Document', 'properties': [{'name': 'schema_version', 'dataType': ['text']}, {'name': 'embedding', 'dataType': ['vector']}]}
    with patch('src.indexing.schema.schema_definition.SchemaDefinition.get_schema', return_value=mock_schema):
        migrator._migrate_schema()
    mock_weaviate_client.schema.create_class.assert_called_once_with(mock_schema)