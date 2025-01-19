"""Excel document processor implementation.

This module provides functionality for processing Excel documents, including:
- Sheet validation and filtering
- Data extraction with configurable limits
- Metadata tracking
- Error handling
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Set

import pandas as pd

from src.ml.processing.document.base import BaseDocumentProcessor, ProcessingResult
from src.ml.processing.document.config import DocumentProcessingConfig, ExcelProcessingConfig
from src.ml.processing.document.errors import DocumentProcessingError, DocumentValidationError


class ExcelProcessor(BaseDocumentProcessor):
    """Processor for Excel documents (.xlsx, .xls, .csv).

    Handles extraction of tabular data with configurable limits on rows,
    columns, and specific sheet selection.

    Args:
        config: Document processing configuration
        logger: Optional logger instance
    """

    def __init__(
        self,
        config: Optional[DocumentProcessingConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._excel_config = config.excel_config if config else ExcelProcessingConfig()
        self._processed_sheets: Dict[str, pd.DataFrame] = {}

    def _initialize_resources(self) -> None:
        """Initialize processor resources."""
        self._processed_sheets.clear()
        self.logger.info("Excel processor initialized")

    def _cleanup_resources(self) -> None:
        """Clean up processor resources."""
        self._processed_sheets.clear()
        self.logger.info("Excel processor cleaned up")

    def _process_document(self, file_path: Path) -> ProcessingResult:
        """Process an Excel document.

        Args:
            file_path: Path to Excel file

        Returns:
            ProcessingResult containing extracted data and metadata

        Raises:
            DocumentProcessingError: If processing fails
            DocumentValidationError: If document validation fails
        """
        try:
            # Read Excel file
            if file_path.suffix == ".csv":
                sheets = {"Sheet1": pd.read_csv(file_path)}
            else:
                sheets = pd.read_excel(file_path, sheet_name=None)

            # Filter and validate sheets
            processed_data = self._process_sheets(sheets)

            # Extract metadata
            metadata = {
                "sheet_count": len(processed_data),
                "total_rows": sum(df.shape[0] for df in processed_data.values()),
                "total_cols": sum(df.shape[1] for df in processed_data.values()),
            }

            return ProcessingResult(
                status="success",
                content={
                    "data": processed_data,
                    "metadata": metadata,
                },
            )

        except Exception as e:
            self.logger.exception(f"Failed to process Excel file {file_path}: {str(e)}")
            return ProcessingResult(status="error", errors=[str(e)])

    def _process_sheets(self, sheets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Process Excel sheets according to configuration.

        Args:
            sheets: Dictionary of sheet names to DataFrames

        Returns:
            Dict of processed sheet data

        Raises:
            DocumentValidationError: If sheet validation fails
        """
        processed: Dict[str, pd.DataFrame] = {}
        target_sheets = self._get_target_sheets(set(sheets.keys()))

        for sheet_name in target_sheets:
            df = sheets[sheet_name]

            # Apply row and column limits
            if self._excel_config.max_rows > 0:
                df = df.iloc[: self._excel_config.max_rows]
            if self._excel_config.max_cols > 0:
                df = df.iloc[:, : self._excel_config.max_cols]

            # Handle empty cells
            if self._excel_config.skip_empty:
                df = df.dropna(how="all")

            # Validate required columns
            if self._excel_config.required_columns:
                missing = set(self._excel_config.required_columns) - set(df.columns)
                if missing:
                    raise DocumentValidationError(
                        f"Missing required columns in sheet {sheet_name}: {missing}"
                    )

            processed[sheet_name] = df

        return processed

    def _get_target_sheets(self, available_sheets: Set[str]) -> Set[str]:
        """Get sheets to process based on configuration.

        Args:
            available_sheets: Set of available sheet names

        Returns:
            Set of sheet names to process

        Raises:
            DocumentValidationError: If specified sheets don't exist
        """
        if not self._excel_config.sheet_names:
            return available_sheets

        missing = self._excel_config.sheet_names - available_sheets
        if missing:
            raise DocumentValidationError(f"Specified sheets not found: {missing}")

        return self._excel_config.sheet_names
