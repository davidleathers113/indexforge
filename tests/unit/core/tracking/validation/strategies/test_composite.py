"""Tests for the composite validation strategy.

This module contains tests for the CompositeValidator class, which combines multiple
validation strategies to perform comprehensive validation of document lineage data.
"""

from typing import List
from unittest.mock import Mock, call

import pytest

from src.core.models import DocumentLineage
from src.core.tracking.validation.composite import CompositeValidator
from src.core.tracking.validation.interface import ValidationStrategy
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator
from src.core.tracking.validation.strategies.circular import CircularDependencyValidator
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


class MockStrategy(ValidationStrategy):
    """Mock validation strategy for testing."""

    def __init__(self, errors: List[str] = None) -> None:
        """Initialize with predefined errors to return."""
        self.errors = errors or []
        self.validate_called = False

    def validate(self, lineage: DocumentLineage) -> List[str]:
        """Return predefined errors and mark as called."""
        self.validate_called = True
        return self.errors


@pytest.fixture
def mock_strategy() -> MockStrategy:
    """Create a mock strategy that returns no errors."""
    return MockStrategy()


@pytest.fixture
def mock_strategy_with_errors() -> MockStrategy:
    """Create a mock strategy that returns validation errors."""
    return MockStrategy(["Error 1", "Error 2"])


@pytest.fixture
def validator() -> CompositeValidator:
    """Create an empty composite validator for testing."""
    return CompositeValidator()


@pytest.fixture
def validator_with_mock(mock_strategy: MockStrategy) -> CompositeValidator:
    """Create a composite validator with a mock strategy."""
    return CompositeValidator([mock_strategy])


def test_init_empty():
    """Test initialization with no strategies."""
    validator = CompositeValidator()
    assert len(validator.strategies) == 0


def test_init_with_strategies(mock_strategy: MockStrategy):
    """Test initialization with strategies.

    Should store provided strategies in the validator.
    """
    validator = CompositeValidator([mock_strategy])
    assert len(validator.strategies) == 1
    assert validator.strategies[0] == mock_strategy


def test_add_strategy(validator: CompositeValidator, mock_strategy: MockStrategy):
    """Test adding a strategy to the validator.

    Should successfully add valid strategy.
    """
    validator.add_strategy(mock_strategy)
    assert len(validator.strategies) == 1
    assert validator.strategies[0] == mock_strategy


def test_add_invalid_strategy(validator: CompositeValidator):
    """Test adding an invalid strategy.

    Should raise TypeError for invalid strategy.
    """
    with pytest.raises(TypeError):
        validator.add_strategy(object())  # Not a ValidationStrategy


def test_remove_strategy(validator: CompositeValidator, mock_strategy: MockStrategy):
    """Test removing a strategy from the validator.

    Should successfully remove existing strategy.
    """
    validator.add_strategy(mock_strategy)
    validator.remove_strategy(mock_strategy)
    assert len(validator.strategies) == 0


def test_remove_nonexistent_strategy(validator: CompositeValidator, mock_strategy: MockStrategy):
    """Test removing a strategy that doesn't exist.

    Should raise ValueError for non-existent strategy.
    """
    with pytest.raises(ValueError):
        validator.remove_strategy(mock_strategy)


def test_validate_empty_lineage(validator_with_mock: CompositeValidator):
    """Test validation with empty lineage data.

    Should return empty list and not call strategies.
    """
    errors = validator_with_mock.validate(None)
    assert not errors
    assert not validator_with_mock.strategies[0].validate_called


def test_validate_no_errors(validator_with_mock: CompositeValidator):
    """Test validation when strategy returns no errors.

    Should return empty list when no errors found.
    """
    document = DocumentLineage(document_id="test-doc")
    errors = validator_with_mock.validate(document)
    assert not errors
    assert validator_with_mock.strategies[0].validate_called


def test_validate_with_errors(
    validator: CompositeValidator, mock_strategy_with_errors: MockStrategy
):
    """Test validation when strategy returns errors.

    Should return all errors from strategy.
    """
    validator.add_strategy(mock_strategy_with_errors)
    document = DocumentLineage(document_id="test-doc")
    errors = validator.validate(document)
    assert len(errors) == 2
    assert all(error in errors for error in mock_strategy_with_errors.errors)


def test_validate_multiple_strategies(
    validator: CompositeValidator,
    mock_strategy: MockStrategy,
    mock_strategy_with_errors: MockStrategy,
):
    """Test validation with multiple strategies.

    Should combine errors from all strategies.
    """
    validator.add_strategy(mock_strategy)
    validator.add_strategy(mock_strategy_with_errors)
    document = DocumentLineage(document_id="test-doc")
    errors = validator.validate(document)
    assert len(errors) == 2
    assert all(error in errors for error in mock_strategy_with_errors.errors)


def test_validate_strategy_exception():
    """Test validation when strategy raises exception.

    Should handle exceptions gracefully and include error message.
    """
    error_message = "Test error"
    mock_strategy = Mock(spec=ValidationStrategy)
    mock_strategy.validate.side_effect = Exception(error_message)

    validator = CompositeValidator([mock_strategy])
    document = DocumentLineage(document_id="test-doc")
    errors = validator.validate(document)

    assert len(errors) == 1
    assert error_message in errors[0]


def test_create_default():
    """Test creation of default composite validator.

    Should create validator with all default strategies.
    """
    validator = CompositeValidator.create_default()
    assert len(validator.strategies) == 3
    assert any(isinstance(s, CircularDependencyValidator) for s in validator.strategies)
    assert any(isinstance(s, ChunkReferenceValidator) for s in validator.strategies)
    assert any(isinstance(s, RelationshipValidator) for s in validator.strategies)


def test_validate_all_default_strategies():
    """Test validation using all default strategies.

    Should execute all default strategies successfully.
    """
    validator = CompositeValidator.create_default()
    document = DocumentLineage(document_id="test-doc")
    errors = validator.validate(document)

    # No errors expected for simple valid document
    assert not errors


def test_validate_strategy_order():
    """Test that strategies are executed in order.

    Should execute strategies in the order they were added.
    """
    mock1 = Mock(spec=ValidationStrategy)
    mock2 = Mock(spec=ValidationStrategy)
    mock1.validate.return_value = []
    mock2.validate.return_value = []

    validator = CompositeValidator([mock1, mock2])
    document = DocumentLineage(document_id="test-doc")
    validator.validate(document)

    # Check call order
    mock1.validate.assert_called_once_with(document)
    mock2.validate.assert_called_once_with(document)
    assert mock1.validate.call_args.args[0] == document
    assert mock2.validate.call_args.args[0] == document
