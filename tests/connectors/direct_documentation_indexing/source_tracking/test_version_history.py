"""Tests for version history tracking functionality."""
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.version_history import (
    ChangeType,
    VersionHistory,
)


@pytest.fixture
def temp_history_dir(tmp_path):
    """Create a temporary directory for test history."""
    return tmp_path / 'history'

@pytest.fixture
def sample_change() -> Dict[str, Any]:
    """Sample change data."""
    return {'change_type': ChangeType.SCHEMA.value, 'description': 'Updated schema configuration', 'author': 'test_user', 'previous_value': {'class': 'OldClass'}, 'new_value': {'class': 'NewClass'}, 'timestamp': datetime.now(timezone.utc).isoformat()}

@pytest.fixture
def sample_tag() -> Dict[str, Any]:
    """Sample version tag data."""
    return {'tag': 'v1.0.0', 'description': 'Initial release', 'author': 'test_user', 'change_type': ChangeType.CONFIG.value, 'timestamp': datetime.now(timezone.utc).isoformat(), 'reliability_score': 0.85}

@pytest.fixture
def existing_history(temp_history_dir, sample_change, sample_tag):
    """Create existing history files."""
    temp_history_dir.mkdir(parents=True)
    history_path = temp_history_dir / 'word_test_source_history.json'
    with open(history_path, 'w') as f:
        json.dump([sample_change], f)
    tags_path = temp_history_dir / 'word_test_source_tags.json'
    with open(tags_path, 'w') as f:
        json.dump({'v1.0.0': sample_tag}, f)
    return {'changes': [sample_change], 'tags': {'v1.0.0': sample_tag}}

def test_version_history_initialization():
    """Test basic initialization of VersionHistory."""
    history = VersionHistory('word', 'test_source')
    assert isinstance(history.changes, list)
    assert isinstance(history.tags, dict)
    assert len(history.changes) == 0
    assert len(history.tags) == 0

def test_load_existing_history(temp_history_dir, existing_history):
    """Test loading existing history from files."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    assert len(history.changes) == 1
    assert len(history.tags) == 1
    assert history.changes[0].change_type == ChangeType.SCHEMA
    assert 'v1.0.0' in history.tags

def test_record_change(temp_history_dir):
    """Test recording a new change."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    history.record_change(change_type=ChangeType.SCHEMA, description='Test change', author='test_user', previous_value={'old': 'value'}, new_value={'new': 'value'})
    assert len(history.changes) == 1
    change = history.changes[0]
    assert change.change_type == ChangeType.SCHEMA
    assert change.description == 'Test change'
    assert change.previous_value == {'old': 'value'}
    assert change.new_value == {'new': 'value'}

def test_create_tag(temp_history_dir):
    """Test creating a version tag."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    history.record_change(change_type=ChangeType.CONFIG, description='Test change', author='test_user', previous_value={}, new_value={})
    history.create_tag(tag='v1.0.0', description='Test tag', author='test_user', change_type=ChangeType.CONFIG, reliability_score=0.9)
    assert 'v1.0.0' in history.tags
    tag = history.tags['v1.0.0']
    assert tag.description == 'Test tag'
    assert tag.reliability_score == 0.9
    assert history.changes[0].version_tag == 'v1.0.0'

def test_get_changes_filtered(temp_history_dir):
    """Test getting filtered changes."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    history.record_change(change_type=ChangeType.SCHEMA, description='Schema change', author='test_user', previous_value={}, new_value={})
    history.record_change(change_type=ChangeType.CONFIG, description='Config change', author='test_user', previous_value={}, new_value={})
    schema_changes = history.get_changes(change_type=ChangeType.SCHEMA)
    assert len(schema_changes) == 1
    assert schema_changes[0].change_type == ChangeType.SCHEMA
    recent_changes = history.get_changes(start_time=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert len(recent_changes) == 2

def test_get_diff(temp_history_dir):
    """Test generating diffs between values."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    previous = {'class': 'OldClass', 'properties': {'field1': 'value1'}}
    new = {'class': 'NewClass', 'properties': {'field1': 'value1', 'field2': 'value2'}}
    diff = history.get_diff(previous, new)
    assert len(diff) > 0
    assert any(('-  "class": "OldClass"' in line for line in diff))
    assert any(('+  "class": "NewClass"' in line for line in diff))
    assert any(('+    "field2": "value2"' in line for line in diff))

def test_version_tag_lookup(temp_history_dir):
    """Test looking up changes by version tag."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    history.record_change(change_type=ChangeType.SCHEMA, description='Tagged change', author='test_user', previous_value={}, new_value={})
    history.create_tag(tag='v1.0.0', description='Test version', author='test_user', change_type=ChangeType.SCHEMA)
    change = history.get_version_at_tag('v1.0.0')
    assert change is not None
    assert change.description == 'Tagged change'
    assert change.version_tag == 'v1.0.0'

def test_get_tags_between(temp_history_dir):
    """Test getting tags within a time range."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir))
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    history.record_change(change_type=ChangeType.SCHEMA, description='Old change', author='test_user', previous_value={}, new_value={})
    history.create_tag(tag='v1.0.0', description='Old version', author='test_user', change_type=ChangeType.SCHEMA)
    tags = history.get_tags_between(start_time=past_time, end_time=future_time)
    assert len(tags) == 1
    assert tags[0].tag == 'v1.0.0'

def test_max_changes_limit(temp_history_dir):
    """Test that max_changes limit is enforced."""
    history = VersionHistory('word', 'test_source', str(temp_history_dir), max_changes=2)
    for i in range(3):
        history.record_change(change_type=ChangeType.SCHEMA, description=f'Change {i}', author='test_user', previous_value={}, new_value={})
    assert len(history.changes) == 2
    assert history.changes[-1].description == 'Change 2'