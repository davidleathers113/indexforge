"""Mock schema migrator fixture."""

from dataclasses import dataclass
import logging
from unittest.mock import MagicMock, patch

import pytest

from ..core.base import BaseState
from ..data.vector import mock_weaviate_client

logger = logging.getLogger(__name__)


@dataclass
class MigratorState(BaseState):
    """Schema migrator state."""

    class_name: str = "Document"
    needs_migration: bool = False
    schema_created: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.needs_migration = False
        self.schema_created = False


@pytest.fixture
def mock_schema_migrator(mock_schema_validator, mock_weaviate_client):
    """Mock schema migrator for testing."""
    mock_migrator = MagicMock()
    state = MigratorState()

    # Set dependencies
    mock_migrator.validator = mock_schema_validator
    mock_migrator.client = mock_weaviate_client
    mock_migrator.class_name = state.class_name

    def mock_ensure_schema():
        """Ensure schema exists and is up to date."""
        try:
            schema = mock_schema_validator.get_schema()

            if not schema:
                # Create new schema
                from src.indexing.schema.schema_definition import SchemaDefinition

                test_schema = SchemaDefinition.get_schema(state.class_name)

                if not mock_schema_validator.validate_schema(test_schema):
                    state.add_error("Schema validation failed")
                    raise ValueError("Invalid schema configuration")

                mock_weaviate_client.schema.create_class(test_schema)
                state.schema_created = True

            elif not mock_schema_validator.check_schema_version():
                # Migrate existing schema
                mock_weaviate_client.schema.delete_class(state.class_name)
                mock_weaviate_client.schema.create_class({"class": state.class_name})
                state.needs_migration = True

        except Exception as e:
            state.add_error(f"Error ensuring schema: {str(e)}")
            raise

    # Configure mock methods
    mock_migrator.ensure_schema = MagicMock(side_effect=mock_ensure_schema)
    mock_migrator.get_errors = state.get_errors
    mock_migrator.reset = state.reset

    yield mock_migrator
    state.reset()


@pytest.fixture(autouse=True)
def mock_schema_classes(mock_schema_migrator):
    """Mock schema-related classes to use fixtures."""
    with (
        patch(
            "src.indexing.schema.schema_migrator.SchemaMigrator",
            return_value=mock_schema_migrator,
        ),
        patch("weaviate.Client", return_value=mock_weaviate_client),
    ):
        yield
