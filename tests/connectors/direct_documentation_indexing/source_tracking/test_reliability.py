"""Tests for source reliability tracking functionality."""
from datetime import UTC, datetime
import json
import time
from typing import Any
from unittest.mock import Mock

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.reliability import (
    ReliabilityMetrics,
    SourceReliability,
)


@pytest.fixture
def temp_metrics_dir(tmp_path):
    """Create a temporary directory for test metrics."""
    return tmp_path / 'metrics'


@pytest.fixture
def sample_content_metrics() -> dict[str, float]:
    """Sample content quality metrics."""
    return {'completeness': 0.8, 'consistency': 0.7, 'readability': 0.9, 'accuracy': 0.85}


@pytest.fixture
def sample_authority_metrics() -> dict[str, float]:
    """Sample authority metrics."""
    return {'reputation': 0.9, 'verification': 0.8, 'expertise': 0.85, 'trust': 0.95}


@pytest.fixture
def existing_metrics(temp_metrics_dir) -> dict[str, Any]:
    """Create existing metrics file."""
    metrics = {'authority_score': 0.75, 'content_quality_score': 0.8, 'update_frequency': 0.5, 'last_update': datetime.now(UTC).isoformat(), 'total_updates': 10, 'quality_checks': {'completeness': 0.8, 'consistency': 0.7}, 'metadata_completeness': 0.9}
    temp_metrics_dir.mkdir(parents=True)
    metrics_path = temp_metrics_dir / 'word_test_source_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f)
    return metrics


@pytest.fixture
def storage():
    """Mock storage for reliability tests."""
    mock_storage = Mock()
    mock_storage.get_lineage.return_value = None
    return mock_storage


def test_source_reliability_initialization():
    """Test basic initialization of SourceReliability."""
    tracker = SourceReliability('word', 'test_source')
    metrics = tracker.metrics
    assert isinstance(metrics, ReliabilityMetrics)
    assert metrics.authority_score == 0.5
    assert metrics.content_quality_score == 0.5
    assert metrics.total_updates == 0


def test_load_existing_metrics(temp_metrics_dir, existing_metrics):
    """Test loading existing metrics from file."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    assert tracker.metrics.authority_score == existing_metrics['authority_score']
    assert tracker.metrics.content_quality_score == existing_metrics['content_quality_score']
    assert tracker.metrics.total_updates == existing_metrics['total_updates']


def test_update_content_quality(temp_metrics_dir, sample_content_metrics):
    """Test updating content quality metrics."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    tracker.update_content_quality(sample_content_metrics)
    assert abs(tracker.metrics.content_quality_score - 0.815) < 0.001
    assert tracker.metrics.quality_checks == sample_content_metrics
    assert tracker.metrics.total_updates == 1


def test_update_metadata_completeness(temp_metrics_dir):
    """Test updating metadata completeness score."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    metadata_fields = ['title', 'author', 'date']
    required_fields = ['title', 'author', 'date', 'version']
    tracker.update_metadata_completeness(metadata_fields, required_fields)
    assert tracker.metrics.metadata_completeness == 0.75


def test_update_authority_score(temp_metrics_dir, sample_authority_metrics):
    """Test updating authority score."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    tracker.update_authority_score(sample_authority_metrics)
    assert abs(tracker.metrics.authority_score - 0.87) < 0.001


def test_update_frequency_calculation(storage):
    """Test calculation of source update frequency."""
    source_id = 'test_source'
    tracker = SourceReliability(storage, source_id)
    tracker.update_content_quality(0.8)
    time.sleep(1)
    tracker.update_content_quality(0.9)
    assert tracker.metrics.total_updates == 2
    assert tracker.metrics.update_frequency > 0
    assert tracker.metrics.update_frequency < 2.0


def test_get_reliability_score(temp_metrics_dir):
    """Test overall reliability score calculation."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    tracker.metrics.authority_score = 0.8
    tracker.metrics.content_quality_score = 0.7
    tracker.metrics.metadata_completeness = 0.9
    tracker.metrics.update_frequency = 0.5
    assert abs(tracker.get_reliability_score() - 0.73) < 0.001


def test_metrics_persistence(temp_metrics_dir, sample_content_metrics):
    """Test that metrics are properly saved to file."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    tracker.update_content_quality(sample_content_metrics)
    new_tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    assert new_tracker.metrics.content_quality_score == tracker.metrics.content_quality_score
    assert new_tracker.metrics.quality_checks == tracker.metrics.quality_checks


def test_get_metrics_summary(temp_metrics_dir):
    """Test metrics summary generation."""
    tracker = SourceReliability('word', 'test_source', str(temp_metrics_dir))
    tracker.update_content_quality({'completeness': 0.8})
    tracker.update_authority_score({'reputation': 0.9})
    summary = tracker.get_metrics_summary()
    assert 'reliability_score' in summary
    assert 'authority_score' in summary
    assert 'content_quality_score' in summary
    assert 'metadata_completeness' in summary
    assert 'update_frequency' in summary
    assert 'quality_checks' in summary