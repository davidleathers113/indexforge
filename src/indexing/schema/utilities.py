"""
Utility functions for schema operations.

This module provides helper functions for schema validation, comparison,
and manipulation. These utilities support the schema definition and
migration processes.
"""


from src.indexing.schema.configurations import CURRENT_SCHEMA_VERSION


def validate_schema_version(schema: dict) -> bool:
    """
    Validate that a schema has a valid version number.

    Args:
        schema (Dict): The schema to validate

    Returns:
        bool: True if the schema version is valid, False otherwise
    """
    try:
        version = next(
            prop["dataType"][0] == "int"
            for prop in schema["properties"]
            if prop["name"] == "schema_version"
        )
        return version is True
    except (KeyError, StopIteration):
        return False


def get_schema_properties(schema: dict) -> set[str]:
    """
    Get a set of property names from a schema.

    Args:
        schema (Dict): The schema to extract properties from

    Returns:
        Set[str]: Set of property names
    """
    try:
        return {prop["name"] for prop in schema["properties"]}
    except (KeyError, TypeError):
        return set()


def compare_schemas(schema1: dict, schema2: dict) -> list[str]:
    """
    Compare two schemas and return a list of differences.

    Args:
        schema1 (Dict): First schema to compare
        schema2 (Dict): Second schema to compare

    Returns:
        List[str]: List of differences between the schemas
    """
    differences = []

    # Compare basic attributes
    for attr in ["class", "vectorizer", "description"]:
        if schema1.get(attr) != schema2.get(attr):
            differences.append(f"Different {attr}")

    # Compare properties
    props1 = get_schema_properties(schema1)
    props2 = get_schema_properties(schema2)

    if props1 != props2:
        added = props2 - props1
        removed = props1 - props2
        if added:
            differences.append(f"Added properties: {', '.join(added)}")
        if removed:
            differences.append(f"Removed properties: {', '.join(removed)}")

    return differences


def get_schema_version(schema: dict) -> int | None:
    """
    Get the version number from a schema.

    Args:
        schema (Dict): The schema to get the version from

    Returns:
        Optional[int]: The schema version number, or None if not found
    """
    try:
        version_prop = next(
            prop for prop in schema["properties"] if prop["name"] == "schema_version"
        )
        return int(version_prop.get("defaultValue", CURRENT_SCHEMA_VERSION))
    except (KeyError, StopIteration, ValueError):
        return None


def needs_migration(schema: dict) -> bool:
    """
    Check if a schema needs migration to the current version.

    Args:
        schema (Dict): The schema to check

    Returns:
        bool: True if the schema needs migration, False otherwise
    """
    current_version = get_schema_version(schema)
    return current_version is None or current_version < CURRENT_SCHEMA_VERSION
