"""Factory classes for creating processor test configurations.

This module provides factory patterns for creating processor instances with
standardized configurations for testing.
"""

from typing import Dict, Type

from src.ml.processing.document.base import ProcessingResult
from src.ml.processing.document.config import (
    DocumentProcessingConfig,
    ExcelProcessingConfig,
    WordProcessingConfig,
)
from src.ml.processing.document.excel import ExcelProcessor
from src.ml.processing.document.word import WordProcessor


class ProcessorTestFactory:
    """Factory for creating processor test configurations."""

    @staticmethod
    def create_word_processor(
        extract_tables: bool = True,
        extract_headers: bool = True,
    ) -> WordProcessor:
        """Create a Word processor with test configuration.

        Args:
            extract_tables: Whether to extract tables
            extract_headers: Whether to extract headers

        Returns:
            Configured WordProcessor instance
        """
        return WordProcessor(
            config=DocumentProcessingConfig(
                word_config=WordProcessingConfig(
                    extract_tables=extract_tables,
                    extract_headers=extract_headers,
                )
            )
        )

    @staticmethod
    def create_excel_processor(
        max_rows: int = 1000,
        max_cols: int = 100,
    ) -> ExcelProcessor:
        """Create an Excel processor with test configuration.

        Args:
            max_rows: Maximum rows to process
            max_cols: Maximum columns to process

        Returns:
            Configured ExcelProcessor instance
        """
        return ExcelProcessor(
            config=DocumentProcessingConfig(
                excel_config=ExcelProcessingConfig(
                    max_rows=max_rows,
                    max_cols=max_cols,
                )
            )
        )

    @classmethod
    def create_all_processors(cls) -> Dict[str, Type[ProcessingResult]]:
        """Create all processor types with default configurations.

        Returns:
            Dictionary of processor instances
        """
        return {
            "word": cls.create_word_processor(),
            "excel": cls.create_excel_processor(),
        }
