"""SQL parsing utilities for monitoring.

This module provides utilities for parsing and analyzing SQL statements.
It includes functions to extract metadata from SQL queries for monitoring purposes.

Features:
- SQL operation type detection (SELECT, INSERT, etc.)
- Table name extraction from queries
- Support for common SQL query patterns
- Case-insensitive parsing
"""

import re
from typing import Literal

# Type definitions
OperationType = Literal["select", "insert", "update", "delete", "other"]


def get_operation_type(statement: str) -> OperationType:
    """Extract operation type from SQL statement.

    Analyzes the SQL statement to determine the type of operation being performed.
    The analysis is case-insensitive and handles basic SQL operations.

    Args:
        statement: SQL statement to analyze

    Returns:
        The type of SQL operation (select, insert, update, delete, or other)

    Example:
        >>> get_operation_type("SELECT * FROM users")
        'select'
        >>> get_operation_type("INSERT INTO users (name) VALUES ('test')")
        'insert'
    """
    statement = statement.strip().lower()
    if statement.startswith("select"):
        return "select"
    elif statement.startswith("insert"):
        return "insert"
    elif statement.startswith("update"):
        return "update"
    elif statement.startswith("delete"):
        return "delete"
    return "other"


def extract_table_name(statement: str) -> str:
    """Extract table name from SQL statement.

    Uses regex patterns to identify and extract the primary table name
    from various types of SQL statements. Handles common SQL patterns
    including SELECT, INSERT, UPDATE, and DELETE statements.

    Args:
        statement: SQL statement to analyze

    Returns:
        Extracted table name or 'unknown' if no table name could be found

    Example:
        >>> extract_table_name("SELECT * FROM users WHERE id = 1")
        'users'
        >>> extract_table_name("INSERT INTO products (name) VALUES ('test')")
        'products'

    Note:
        - The function is case-insensitive
        - Only extracts the main table name (not join tables)
        - Returns 'unknown' if no table name can be determined
        - Does not handle complex cases like subqueries or CTEs
    """
    # Common SQL patterns for table names
    patterns = [
        r"from\s+(\w+)",  # SELECT ... FROM table
        r"insert\s+into\s+(\w+)",  # INSERT INTO table
        r"update\s+(\w+)",  # UPDATE table
        r"delete\s+from\s+(\w+)",  # DELETE FROM table
    ]

    statement = statement.lower()
    for pattern in patterns:
        match = re.search(pattern, statement)
        if match:
            return match.group(1)

    return "unknown"
