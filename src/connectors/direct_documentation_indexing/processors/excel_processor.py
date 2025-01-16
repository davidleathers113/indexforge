"""Excel file processor for document content extraction.

This module provides functionality for processing Excel files (.xlsx, .xls)
and CSV files, extracting their content and metadata in a standardized format.
It handles multiple sheets, data validation, and basic statistics collection.
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .base_processor import BaseProcessor


logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """Processor for Excel and CSV file content extraction.

    This class handles the processing of Excel workbooks and CSV files,
    extracting their content, metadata, and basic statistics. It supports
    configuration options for controlling the processing behavior.

    Attributes:
        SUPPORTED_EXTENSIONS (set): Set of supported file extensions.
        max_rows (Optional[int]): Maximum number of rows to process.
        skip_sheets (set): Set of sheet names to skip.
        required_columns (set): Set of columns that must be present.

    Example:
        ```python
        processor = ExcelProcessor({
            "max_rows": 1000,
            "skip_sheets": ["Internal", "Debug"],
            "required_columns": ["ID", "Name", "Value"]
        })

        if processor.can_process(file_path):
            result = processor.process(file_path)
            if result["status"] == "success":
                sheets = result["content"]["sheets"]
        ```
    """

    SUPPORTED_EXTENSIONS = {".xlsx", ".csv", ".xls"}

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the Excel processor with configuration.

        Sets up the processor with optional configuration parameters that
        control the processing behavior.

        Args:
            config: Optional configuration dictionary containing:
                - max_rows (int): Maximum number of rows to process
                - skip_sheets (List[str]): Sheet names to skip
                - required_columns (List[str]): Columns that must be present

        Example:
            ```python
            processor = ExcelProcessor({
                "max_rows": 1000,
                "skip_sheets": ["Internal"],
                "required_columns": ["ID", "Name"]
            })
            ```
        """
        super().__init__(config)
        self.max_rows = config.get("max_rows", None)
        self.skip_sheets = set(config.get("skip_sheets", []))
        self.required_columns = set(config.get("required_columns", []))

    def can_process(self, file_path: Path) -> bool:
        """Check if the file can be processed by this processor.

        Determines whether the file has a supported extension (.xlsx, .xls, .csv).

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if the file extension is supported, False otherwise.

        Example:
            ```python
            if processor.can_process(Path("data.xlsx")):
                result = processor.process(Path("data.xlsx"))
            ```
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def process(self, file_path: Path) -> dict[str, Any]:
        """Process an Excel or CSV file and extract its content.

        Processes the file, extracting content from all sheets (for Excel)
        or the entire file (for CSV). Collects metadata and basic statistics.

        Args:
            file_path: Path to the Excel or CSV file to process.

        Returns:
            Dict[str, Any]: Processing result containing:
                - status: "success" or "error"
                - content: Dict with sheets data and metadata
                - error: Error message if processing failed

        Raises:
            ValueError: If required columns are missing.
            pd.errors.EmptyDataError: If file is empty.
            Exception: For any other processing errors.

        Example:
            ```python
            result = processor.process(Path("data.xlsx"))
            if result["status"] == "success":
                sheets = result["content"]["sheets"]
                metadata = result["content"]["metadata"]
            else:
                error = result["error"]
            ```
        """
        try:
            metadata = self._get_file_metadata(file_path)

            if file_path.suffix.lower() == ".csv":
                sheets_data = {"Sheet1": self._process_csv(file_path)}
            else:
                sheets_data = self._process_excel(file_path)

            return {"status": "success", "content": {"sheets": sheets_data, "metadata": metadata}}

        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e!s}")
            return {"status": "error", "error": str(e), "content": {"metadata": metadata}}

    def _process_csv(self, file_path: Path) -> dict[str, Any]:
        """Process a CSV file and extract its content.

        Reads and processes a CSV file, applying row limits and column validation
        if configured.

        Args:
            file_path: Path to the CSV file to process.

        Returns:
            Dict[str, Any]: Processed data containing:
                - data: List of row dictionaries
                - stats: Basic statistics about the data

        Raises:
            pd.errors.EmptyDataError: If file is empty.
            ValueError: If required columns are missing.
        """
        df = pd.read_csv(file_path, nrows=self.max_rows, low_memory=False)
        return self._process_dataframe(df)

    def _process_excel(self, file_path: Path) -> dict[str, dict[str, Any]]:
        """Process an Excel workbook with multiple sheets.

        Reads and processes each sheet in the Excel workbook, skipping
        any sheets specified in skip_sheets configuration.

        Args:
            file_path: Path to the Excel file to process.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping sheet names to
            their processed data and statistics.

        Raises:
            ValueError: If required columns are missing in any sheet.
            pd.errors.EmptyDataError: If all sheets are empty.
        """
        sheets_data = {}
        with pd.ExcelFile(file_path) as excel_file:
            for sheet_name in excel_file.sheet_names:
                if sheet_name in self.skip_sheets:
                    continue
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=self.max_rows)
                sheets_data[sheet_name] = self._process_dataframe(df)

        return sheets_data

    def _process_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """Process a pandas DataFrame and extract information.

        Processes a DataFrame, validating required columns, collecting
        statistics, and converting data to a dictionary format.

        Args:
            df: Pandas DataFrame to process.

        Returns:
            Dict[str, Any]: Processed data containing:
                - data: List of row dictionaries
                - stats: Statistics about the data

        Raises:
            ValueError: If required columns are missing.

        Note:
            NaN values in the DataFrame are converted to None in the output.
        """
        # Validate required columns
        if self.required_columns:
            missing_cols = self.required_columns - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

        # Extract basic statistics
        stats = {"row_count": len(df), "column_count": len(df.columns), "columns": list(df.columns)}

        # Convert to dict format, handling NaN values
        data = df.replace({pd.NA: None}).to_dict(orient="records")

        return {"data": data, "stats": stats}
