"""Connector service for managing document processors."""

import logging

from src.connectors.direct_documentation_indexing import (
    DocumentConnector,
    ExcelProcessor,
    WordProcessor,
)


logger = logging.getLogger(__name__)


class ConnectorService:
    """Manages document connectors and processors."""

    @staticmethod
    def setup_connector() -> DocumentConnector:
        """Set up document connector with processors.

        Returns:
            Configured DocumentConnector instance
        """
        connector = DocumentConnector()

        # Configure processors
        excel_config = {
            "max_rows": None,
            "required_columns": [],
            "skip_sheets": [],
        }

        word_config = {
            "extract_headers": True,
            "extract_tables": True,
            "extract_images": False,
        }

        connector.processors = {
            "excel": ExcelProcessor(excel_config),
            "word": WordProcessor(word_config),
        }

        return connector
