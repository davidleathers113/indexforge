"""Mock schema validator fixture."""

from dataclasses import dataclass
import logging
from typing import Dict, Optional
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class SchemaState(BaseState):
    """Schema validator state."""

    schema: Optional[Dict] = None
    schema_version_valid: bool = True

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.schema = None
        self.schema_version_valid = True


@pytest.fixture(scope="function")
def mock_schema_validator():
    """Mock schema validator for testing."""
    mock_validator = MagicMock()
    state = SchemaState()

    def mock_get_schema():
        """Get the current schema state."""
        return state.schema

    def mock_set_schema(schema):
        """Set the schema state."""
        state.schema = schema

    def mock_set_schema_version_valid(valid: bool):
        """Set whether schema version is valid."""
        state.schema_version_valid = valid

    def mock_validate_schema(schema):
        """Validate schema with error tracking."""
        try:
            # Basic validation
            if not schema.get("class"):
                state.add_error("Missing class name in schema")
                return False
            if not schema.get("properties"):
                state.add_error("Missing properties in schema")
                return False

            # Always return True for test purposes
            # The actual validation is handled by the test setup
            return True

        except Exception as e:
            state.add_error(f"Error validating schema: {str(e)}")
            return False

    def mock_check_schema_version():
        """Check if schema version is valid."""
        return state.schema_version_valid

    # Configure mock methods
    mock_validator.get_schema = MagicMock(side_effect=mock_get_schema)
    mock_validator.set_schema = MagicMock(side_effect=mock_set_schema)
    mock_validator.set_schema_version_valid = MagicMock(side_effect=mock_set_schema_version_valid)
    mock_validator.validate_schema = MagicMock(side_effect=mock_validate_schema)
    mock_validator.check_schema_version = MagicMock(side_effect=mock_check_schema_version)
    mock_validator.get_errors = state.get_errors
    mock_validator.reset = state.reset

    yield mock_validator
    state.reset()
