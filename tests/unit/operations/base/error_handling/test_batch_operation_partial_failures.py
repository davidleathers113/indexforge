"""Test batch operation partial failure handling.

Tests scenarios where some operations within a batch fail while others succeed.
"""

from unittest.mock import Mock

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation


class TestPartialFailureBatchOperation(BatchOperation):
    """Test implementation of BatchOperation for partial failure testing."""

    def prepare_item(self, item):
        if item.get("fail_prepare"):
            raise ValueError(f"Preparation failed for item {item['id']}")
        return {"prepared": item}

    def validate_item(self, item):
        return not item.get("fail_validate")

    def process_batch(self, batch):
        results = []
        for item in batch:
            if item.get("fail_process"):
                results.append(
                    {
                        "id": item["id"],
                        "status": "failed",
                        "error": f"Processing failed for item {item['id']}",
                    }
                )
            else:
                results.append({"id": item["id"], "status": "success"})
        return results


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestPartialFailureBatchOperation(collection=mock_collection, batch_size=3)


def test_mixed_success_and_failure(batch_operation):
    """
    Test handling of mixed success and failure in a single batch.

    Given: A batch with both successful and failing items
    When: The batch is processed
    Then: Successes and failures are properly tracked and reported
    """
    items = [
        {"id": "1"},  # Success
        {"id": "2", "fail_process": True},  # Failure
        {"id": "3"},  # Success
    ]

    results = batch_operation.execute_batch(items)

    assert len(results) == 3, "All items should have results"
    assert results[0]["status"] == "success"
    assert results[1]["status"] == "failed"
    assert results[2]["status"] == "success"


def test_partial_validation_failures(batch_operation):
    """
    Test handling of validation failures within a batch.

    Given: A batch where some items fail validation
    When: The batch is processed
    Then: Invalid items are filtered and valid items are processed
    """
    items = [
        {"id": "1"},  # Valid
        {"id": "2", "fail_validate": True},  # Invalid
        {"id": "3"},  # Valid
    ]

    results = batch_operation.execute_batch(items)

    assert len(results) == 2, "Only valid items should be processed"
    assert all(r["status"] == "success" for r in results)


def test_preparation_and_processing_failures(batch_operation):
    """
    Test handling of failures at different stages.

    Given: A batch with items failing at different stages
    When: The batch is processed
    Then: Failures are handled appropriately at each stage
    """
    items = [
        {"id": "1", "fail_prepare": True},  # Fails preparation
        {"id": "2", "fail_process": True},  # Fails processing
        {"id": "3"},  # Succeeds
    ]

    with pytest.raises(ValueError, match="Preparation failed for item 1"):
        batch_operation.execute_batch(items)


def test_error_aggregation(batch_operation):
    """
    Test aggregation of multiple errors in a batch.

    Given: A batch with multiple failing items
    When: The batch is processed
    Then: All errors are properly aggregated and reported
    """
    items = [
        {"id": "1", "fail_process": True},
        {"id": "2", "fail_process": True},
        {"id": "3"},
    ]

    results = batch_operation.execute_batch(items)

    failed_results = [r for r in results if r["status"] == "failed"]
    assert len(failed_results) == 2, "Should track all failures"
    assert all("error" in r for r in failed_results), "All failures should have error messages"


def test_recovery_after_partial_failure(batch_operation):
    """
    Test system recovery after partial batch failures.

    Given: Multiple batches with some failures
    When: Subsequent batches are processed
    Then: System recovers and processes new batches correctly
    """
    # First batch with failures
    items1 = [{"id": "1", "fail_process": True}, {"id": "2"}]
    results1 = batch_operation.execute_batch(items1)
    assert results1[0]["status"] == "failed"
    assert results1[1]["status"] == "success"

    # Second batch should process normally
    items2 = [{"id": "3"}, {"id": "4"}]
    results2 = batch_operation.execute_batch(items2)
    assert all(r["status"] == "success" for r in results2)
