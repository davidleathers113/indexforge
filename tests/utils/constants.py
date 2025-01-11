"""Common test constants."""


__all__ = [
    "SAMPLE_CACHE_KEY",
    "SAMPLE_CACHE_VALUE",
    "SAMPLE_CACHE_TTL",
    "SAMPLE_REDIS_CONFIG",
    "SAMPLE_DOCUMENT",
    "SAMPLE_SCHEMA",
]

# Cache related constants
SAMPLE_CACHE_KEY = "test:sample-key"
SAMPLE_CACHE_VALUE = {"test": "value"}
SAMPLE_CACHE_TTL = 3600

SAMPLE_REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "prefix": "test",
}

# Document related constants
SAMPLE_DOCUMENT = {
    "id": "test-doc-id",
    "content": "Test document content",
    "metadata": {
        "title": "Test Document",
        "created_at": "2024-01-01T00:00:00Z",
    },
}

# Schema related constants
SAMPLE_SCHEMA = {
    "classes": [
        {
            "class": "Document",
            "description": "A document class",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The document content",
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                    "description": "Document metadata",
                },
            ],
        }
    ],
}
