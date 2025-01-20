"""Storage error types.

This module defines the core error types for storage operations.
It provides a hierarchy of exceptions for handling various storage-related errors.
"""


class StorageError(Exception):
    """Base exception for storage-related errors.

    This is the root exception class for all storage-related errors,
    providing a common base for error handling and type checking.
    """

    pass


class DataNotFoundError(StorageError):
    """Raised when requested data is not found.

    This error indicates that an attempt was made to access or manipulate
    data that does not exist in storage.
    """

    pass


class DataCorruptionError(StorageError):
    """Raised when data integrity is compromised.

    This error indicates that stored data has been corrupted or is in an
    invalid state, making it impossible to deserialize or use properly.
    """

    pass
