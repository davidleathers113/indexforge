"""Common types and enums for document models.

This module contains shared types and enums used across different model files
to avoid circular dependencies.
"""

from enum import Enum


class DocumentStatus(Enum):
    """Document processing status."""

    PENDING = "pending"  # Not yet processed
    PROCESSING = "processing"  # Currently being processed
    PROCESSED = "processed"  # Successfully processed
    FAILED = "failed"  # Processing failed
    ARCHIVED = "archived"  # Document archived


class DocumentType(Enum):
    """Types of documents that can be processed."""

    TEXT = "text"  # Plain text documents
    MARKDOWN = "markdown"  # Markdown documents
    HTML = "html"  # HTML documents
    PDF = "pdf"  # PDF documents
    CODE = "code"  # Source code files
    NOTION = "notion"  # Notion workspace exports
