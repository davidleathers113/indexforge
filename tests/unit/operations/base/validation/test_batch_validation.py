"""Test validation functionality for batch operations."""

import pytest

from src.api.repositories.weaviate.exceptions import BatchValidationError
from src.api.repositories.weaviate.operations.base import BatchOperation


@pytest.fixture
def batch_operation():
    """Setup BatchOperation instance."""
    return BatchOperation()


def test_validate_batch_size():
    """
    Test batch size validation.

    Given: A BatchOperation instance
    When: Initializing with invalid batch sizes
    Then: Appropriate validation errors are raised
    """
    with pytest.raises(BatchValidationError, match="Batch size must be positive"):
        BatchOperation(batch_size=0)

    with pytest.raises(BatchValidationError, match="Batch size must be positive"):
        BatchOperation(batch_size=-1)

    # Valid batch size should not raise
    BatchOperation(batch_size=100)


def test_validate_batch_data(batch_operation):
    """
    Test batch data validation.

    Given: A BatchOperation instance
    When: Adding invalid data to batch
    Then: Appropriate validation errors are raised
    """
    with pytest.raises(BatchValidationError, match="Batch data cannot be None"):
        batch_operation.validate_batch_data(None)

    with pytest.raises(BatchValidationError, match="Batch data must be a list"):
        batch_operation.validate_batch_data("not a list")

    # Valid data should not raise
    batch_operation.validate_batch_data([{"id": 1}, {"id": 2}])


def test_validate_required_fields(batch_operation):
    """
    Test required fields validation.

    Given: A BatchOperation instance
    When: Processing data with missing required fields
    Then: Appropriate validation errors are raised
    """
    required_fields = ["id", "name"]
    data = [{"id": 1}, {"name": "test"}]  # Missing name  # Missing id

    with pytest.raises(BatchValidationError, match="Missing required field"):
        batch_operation.validate_required_fields(data, required_fields)

    # Valid data should not raise
    valid_data = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
    batch_operation.validate_required_fields(valid_data, required_fields)


def test_validate_field_types(batch_operation):
    """
    Test field type validation.

    Given: A BatchOperation instance
    When: Processing data with incorrect field types
    Then: Appropriate validation errors are raised
    """
    field_types = {"id": int, "name": str, "active": bool}

    invalid_data = [
        {"id": "1", "name": "test", "active": True},  # id should be int
        {"id": 2, "name": 123, "active": "true"},  # name should be str, active should be bool
    ]

    with pytest.raises(BatchValidationError, match="Invalid field type"):
        batch_operation.validate_field_types(invalid_data, field_types)

    # Valid data should not raise
    valid_data = [
        {"id": 1, "name": "test", "active": True},
        {"id": 2, "name": "test2", "active": False},
    ]
    batch_operation.validate_field_types(valid_data, field_types)


def test_validate_field_constraints(batch_operation):
    """
    Test field constraint validation.

    Given: A BatchOperation instance
    When: Processing data with values violating constraints
    Then: Appropriate validation errors are raised
    """
    constraints = {
        "age": lambda x: 0 <= x <= 120,
        "email": lambda x: "@" in x,
        "score": lambda x: 0.0 <= x <= 1.0,
    }

    invalid_data = [
        {"age": 150, "email": "test@example.com", "score": 0.5},  # Invalid age
        {"age": 25, "email": "invalid-email", "score": 1.5},  # Invalid email and score
    ]

    with pytest.raises(BatchValidationError, match="Field constraint violation"):
        batch_operation.validate_field_constraints(invalid_data, constraints)

    # Valid data should not raise
    valid_data = [
        {"age": 30, "email": "test@example.com", "score": 0.8},
        {"age": 25, "email": "other@example.com", "score": 0.5},
    ]
    batch_operation.validate_field_constraints(valid_data, constraints)


def test_validate_unique_fields(batch_operation):
    """
    Test unique field validation.

    Given: A BatchOperation instance
    When: Processing data with duplicate unique field values
    Then: Appropriate validation errors are raised
    """
    unique_fields = ["id", "email"]

    duplicate_data = [
        {"id": 1, "email": "test@example.com"},
        {"id": 1, "email": "other@example.com"},  # Duplicate id
        {"id": 2, "email": "test@example.com"},  # Duplicate email
    ]

    with pytest.raises(BatchValidationError, match="Duplicate value for unique field"):
        batch_operation.validate_unique_fields(duplicate_data, unique_fields)

    # Valid data should not raise
    valid_data = [{"id": 1, "email": "test1@example.com"}, {"id": 2, "email": "test2@example.com"}]
    batch_operation.validate_unique_fields(valid_data, unique_fields)


def test_validate_field_relationships(batch_operation):
    """
    Test field relationship validation.

    Given: A BatchOperation instance
    When: Processing data with invalid field relationships
    Then: Appropriate validation errors are raised
    """
    relationships = [
        lambda x: x["end_date"] > x["start_date"],
        lambda x: x["max_value"] >= x["min_value"],
    ]

    invalid_data = [
        {
            "start_date": "2023-01-01",
            "end_date": "2022-12-31",  # End before start
            "min_value": 100,
            "max_value": 50,  # Max less than min
        }
    ]

    with pytest.raises(BatchValidationError, match="Invalid field relationship"):
        batch_operation.validate_field_relationships(invalid_data, relationships)

    # Valid data should not raise
    valid_data = [
        {"start_date": "2023-01-01", "end_date": "2023-12-31", "min_value": 50, "max_value": 100}
    ]
    batch_operation.validate_field_relationships(valid_data, relationships)
