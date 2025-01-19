"""Import sorter formatter."""

import logging

import isort

from .base_formatter import BaseFormatter


logger = logging.getLogger(__name__)


class ImportSorter(BaseFormatter):
    """Sorts imports using isort."""

    def __init__(self, config: dict):
        """Initialize with isort configuration.

        Args:
            config: Isort configuration settings
        """
        self.config = config

    def format(self, content: str) -> str:
        """Sort imports in the content.

        Args:
            content: Content to process

        Returns:
            str: Content with sorted imports
        """
        try:
            return isort.code(content, **self.config)
        except Exception as e:
            logger.error("Import sorting failed: %s", str(e))
            return content
