import json
from pathlib import Path
from typing import Any, Dict
import pytest
from src.connectors.direct_documentation_indexing.source_tracking import SourceTracker, TenantSourceTracker

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for test configs."""
    return tmp_path / 'configs'

@pytest.fixture
def temp_tenant_config_dir(tmp_path):
    """Create a temporary directory for tenant configs."""
    return tmp_path / 'tenant_configs'

@pytest.fixture
def word_source_config() -> Dict[str, Any]:
    """Sample Word document source configuration."""
    return {'schema_variations': {'class': 'WordDocument', 'description': 'Document from word source', 'vectorizer': 'text2vec-transformers'}, 'custom_properties': {'word_metadata': {'dataType': ['text'], 'description': 'Word document specific metadata'}, 'headers': {'dataType': ['text[]'], 'description': 'Document headers'}}, 'vectorizer_settings': {'model': 'sentence-transformers-all-MiniLM-L6-v2', 'poolingStrategy': 'mean'}, 'cross_source_mappings': {'excel': 'document_id'}}

@pytest.fixture
def tenant_config() -> Dict[str, Any]:
    """Sample tenant configuration."""
    return {'tenant_id': 'test_tenant', 'schema_overrides': {'description': 'Custom tenant description'}, 'property_overrides': {'custom_field': {'dataType': ['text'], 'description': 'Tenant-specific field'}}, 'vectorizer_overrides': {'model': 'custom-model'}, 'cross_tenant_search': True, 'isolation_level': 'flexible'}

def test_source_tracker_default_config():
    """Test SourceTracker with default configuration."""
    tracker = SourceTracker('word')
    schema = tracker.get_schema()
    assert schema['class'] == 'WordDocument'
    assert 'content' in schema['properties']
    assert 'source_id' in schema['properties']
    assert schema['moduleConfig']['text2vec-transformers']['model'] == 'sentence-transformers-all-MiniLM-L6-v2'

def test_source_tracker_custom_config(temp_config_dir, word_source_config):
    """Test SourceTracker with custom configuration."""
    config_dir = temp_config_dir
    config_dir.mkdir(parents=True)
    config_path = config_dir / 'word_config.json'
    with open(config_path, 'w') as f:
        json.dump(word_source_config, f)
    tracker = SourceTracker('word', str(config_dir))
    schema = tracker.get_schema()
    assert schema['class'] == 'WordDocument'
    assert 'word_metadata' in schema['properties']
    assert 'headers' in schema['properties']
    assert tracker.get_cross_source_mappings()['excel'] == 'document_id'

def test_source_tracker_schema_validation():
    """Test schema validation in SourceTracker."""
    tracker = SourceTracker('word')
    errors = tracker.validate_schema()
    assert not errors

def test_tenant_source_tracker_default_config():
    """Test TenantSourceTracker with default configuration."""
    tracker = TenantSourceTracker('test_tenant', 'word')
    schema = tracker.get_schema()
    assert 'tenant_id' in schema['properties']
    assert not tracker.is_cross_tenant_search_enabled()
    assert tracker.get_isolation_level() == 'strict'

def test_tenant_source_tracker_custom_config(temp_config_dir, temp_tenant_config_dir, word_source_config, tenant_config):
    """Test TenantSourceTracker with custom configuration."""
    source_config_dir = temp_config_dir
    source_config_dir.mkdir(parents=True)
    source_config_path = source_config_dir / 'word_config.json'
    with open(source_config_path, 'w') as f:
        json.dump(word_source_config, f)
    tenant_config_dir = temp_tenant_config_dir
    tenant_config_dir.mkdir(parents=True)
    tenant_config_path = tenant_config_dir / 'test_tenant_config.json'
    with open(tenant_config_path, 'w') as f:
        json.dump(tenant_config, f)
    tracker = TenantSourceTracker('test_tenant', 'word', str(source_config_dir), str(tenant_config_dir))
    schema = tracker.get_schema()
    assert schema['description'] == 'Custom tenant description'
    assert 'custom_field' in schema['properties']
    assert schema['moduleConfig']['text2vec-transformers']['model'] == 'custom-model'
    assert tracker.is_cross_tenant_search_enabled()
    assert tracker.get_isolation_level() == 'flexible'

def test_tenant_source_tracker_search_filters():
    """Test search filter generation for tenant isolation."""
    tracker = TenantSourceTracker('test_tenant', 'word')
    filters = tracker.get_search_filters()
    assert filters['tenant_id'] == 'test_tenant'

def test_tenant_source_tracker_config_update(temp_tenant_config_dir):
    """Test tenant configuration updates."""
    config_dir = temp_tenant_config_dir
    config_dir.mkdir(parents=True)
    tracker = TenantSourceTracker('test_tenant', 'word', tenant_config_dir=str(config_dir))
    updates = {'cross_tenant_search': True, 'isolation_level': 'flexible'}
    tracker.update_tenant_config(updates)
    assert tracker.is_cross_tenant_search_enabled()
    assert tracker.get_isolation_level() == 'flexible'
    config_path = config_dir / 'test_tenant_config.json'
    assert config_path.exists()
    with open(config_path, 'r') as f:
        saved_config = json.load(f)
        assert saved_config['cross_tenant_search'] is True
        assert saved_config['isolation_level'] == 'flexible'