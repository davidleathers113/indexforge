"""Excel document processor for ML pipeline.

This module provides specialized processing for Excel documents (.xlsx, .xls).
It handles extraction of text content and metadata from Excel files while
maintaining sheet structure information.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from pydantic import Field

from .base import BaseProcessor
from .config.settings import PipelineConfig, ProcessingConfig


class ExcelProcessingConfig(ProcessingConfig):
    """Configuration for Excel document processing.

    Extends the base ProcessingConfig with Excel-specific settings.
    """

    sheet_names: Optional[List[str]] = Field(
        default=None, description="List of sheet names to process. If None, processes all sheets."
    )
    header_row: int = Field(
        default=0, description="Row number to use as column headers (0-based)", ge=0
    )
    skip_empty: bool = Field(default=True, description="Whether to skip empty sheets")
    max_sheet_size: int = Field(
        default=1000000, description="Maximum number of cells to process per sheet", gt=0
    )


class ExcelProcessor(BaseProcessor):
    """Processor for Excel documents.

    Handles the extraction and processing of content from Excel files,
    maintaining sheet structure and handling large files efficiently.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        processing_config: Optional[ExcelProcessingConfig] = None,
    ) -> None:
        """Initialize the Excel processor.

        Args:
            config: Optional pipeline configuration
            processing_config: Optional Excel-specific processing configuration
        """
        super().__init__(
            config=config, processing_config=processing_config or ExcelProcessingConfig()
        )
        self._excel_config: ExcelProcessingConfig = self.processing_config  # type: ignore
        self._processed_files: Set[Path] = set()

    def _validate_config(self) -> None:
        """Validate the processor configuration.

        Extends the base validation to ensure Excel-specific config is valid.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(self.processing_config, ExcelProcessingConfig):
            raise ValueError("processing_config must be an instance of ExcelProcessingConfig")

    def initialize(self) -> None:
        """Initialize the processor.

        Performs Excel-specific initialization tasks.
        """
        super().initialize()
        self._processed_files.clear()

    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process an Excel file.

        Args:
            file_path: Path to the Excel file to process

        Returns:
            Dict containing:
                - content: Extracted text content
                - metadata: File and processing metadata
                - sheets: Sheet-specific information

        Raises:
            RuntimeError: If the processor is not initialized
            ValueError: If the file is invalid or cannot be processed
            IOError: If there are issues reading the file
        """
        super().process(file_path)

        if not isinstance(file_path, Path):
            raise ValueError("file_path must be a Path object")

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            sheets_to_process = self._excel_config.sheet_names or excel_file.sheet_names

            processed_sheets = []
            total_content = []

            for sheet_name in sheets_to_process:
                if sheet_name not in excel_file.sheet_names:
                    continue

                # Read sheet
                df = pd.read_excel(
                    excel_file, sheet_name=sheet_name, header=self._excel_config.header_row
                )

                # Skip empty sheets if configured
                if self._excel_config.skip_empty and df.empty:
                    continue

                # Validate sheet size
                if df.size > self._excel_config.max_sheet_size:
                    raise ValueError(
                        f"Sheet '{sheet_name}' exceeds maximum size of "
                        f"{self._excel_config.max_sheet_size} cells"
                    )

                # Process sheet content
                sheet_content = self._process_sheet(df, sheet_name)
                total_content.extend(sheet_content["content"])
                processed_sheets.append(sheet_content)

            # Update processed files tracking
            self._processed_files.add(file_path)

            return {
                "content": " ".join(total_content),
                "metadata": {
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower(),
                    "total_sheets": len(processed_sheets),
                    "processed_sheets": [s["name"] for s in processed_sheets],
                },
                "sheets": processed_sheets,
            }

        except Exception as e:
            raise ValueError(f"Error processing Excel file: {str(e)}") from e

    def _process_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Process a single sheet from the Excel file.

        Args:
            df: Pandas DataFrame containing the sheet data
            sheet_name: Name of the sheet being processed

        Returns:
            Dict containing sheet-specific information and content
        """
        # Convert headers and content to strings, handling non-string types
        headers = [str(col) for col in df.columns]

        # Process cell contents, converting to string and handling NaN/None
        content = []
        for _, row in df.iterrows():
            row_content = []
            for header, value in zip(headers, row):
                if pd.notna(value):  # Skip NaN/None values
                    row_content.append(f"{header}: {value}")
            if row_content:  # Only add non-empty rows
                content.append(" | ".join(row_content))

        return {
            "name": sheet_name,
            "headers": headers,
            "row_count": len(df),
            "column_count": len(df.columns),
            "content": content,
        }

    def cleanup(self) -> None:
        """Clean up processor resources.

        Performs Excel-specific cleanup tasks.
        """
        self._processed_files.clear()
        super().cleanup()

    @property
    def processed_files(self) -> Set[Path]:
        """Get the set of processed file paths.

        Returns:
            Set of Path objects for processed files
        """
        return self._processed_files.copy()
