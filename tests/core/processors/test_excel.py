"""Tests for Excel file processor functionality.

This module contains tests for the ExcelProcessor class, covering both Excel
and CSV file processing capabilities, including configuration options,
data validation, and error handling.
"""

import logging
from pathlib import Path

from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
import pandas as pd
import pytest

from src.core.processors.excel import ExcelProcessor


# Configure logging for tests
logger = logging.getLogger(__name__)


@pytest.fixture
def excel_processor(request: FixtureRequest, caplog: LogCaptureFixture):
    """Fixture providing a default Excel processor instance.

    Args:
        request: Pytest request object for test context
        caplog: Fixture for capturing log messages

    Returns:
        ExcelProcessor: Default processor instance
    """
    caplog.set_level(logging.DEBUG)
    logger.info("Creating default Excel processor for test: %s", request.node.name)
    processor = ExcelProcessor()
    yield processor
    logger.info("Cleaning up Excel processor for test: %s", request.node.name)


@pytest.fixture
def configured_processor(request: FixtureRequest, caplog: LogCaptureFixture):
    """Fixture providing a configured Excel processor instance.

    Args:
        request: Pytest request object for test context
        caplog: Fixture for capturing log messages

    Returns:
        ExcelProcessor: Configured processor instance
    """
    caplog.set_level(logging.DEBUG)
    config = {"max_rows": 100, "skip_sheets": ["Internal"], "required_columns": ["ID", "Name"]}
    logger.info(
        "Creating configured Excel processor for test: %s with config: %s",
        request.node.name,
        config,
    )
    processor = ExcelProcessor(config)
    yield processor
    logger.info("Cleaning up configured Excel processor for test: %s", request.node.name)


@pytest.fixture
def sample_df():
    """Fixture providing a sample DataFrame for testing.

    Returns:
        pd.DataFrame: Sample data frame with test data
    """
    logger.debug("Creating sample DataFrame for testing")
    df = pd.DataFrame(
        {"ID": [1, 2, 3], "Name": ["Test1", "Test2", "Test3"], "Value": [10.0, 20.0, 30.0]}
    )
    logger.debug("Created DataFrame with shape: %s", df.shape)
    return df


@pytest.fixture
def excel_file(tmp_path: Path, sample_df: pd.DataFrame, request: FixtureRequest):
    """Fixture providing a test Excel file.

    Args:
        tmp_path: Temporary directory path
        sample_df: Sample DataFrame to write
        request: Pytest request object for test context

    Returns:
        Path: Path to test Excel file
    """
    logger.info("Creating test Excel file for test: %s", request.node.name)
    file_path = tmp_path / "test.xlsx"

    logger.debug("Writing DataFrame to Excel file: %s", file_path)
    with pd.ExcelWriter(file_path) as writer:
        sample_df.to_excel(writer, sheet_name="Sheet1", index=False)
        sample_df.to_excel(writer, sheet_name="Sheet2", index=False)

    logger.debug("Excel file created successfully")
    return file_path


@pytest.fixture
def csv_file(tmp_path: Path, sample_df: pd.DataFrame, request: FixtureRequest):
    """Fixture providing a test CSV file.

    Args:
        tmp_path: Temporary directory path
        sample_df: Sample DataFrame to write
        request: Pytest request object for test context

    Returns:
        Path: Path to test CSV file
    """
    logger.info("Creating test CSV file for test: %s", request.node.name)
    file_path = tmp_path / "test.csv"

    logger.debug("Writing DataFrame to CSV file: %s", file_path)
    sample_df.to_csv(file_path, index=False)

    logger.debug("CSV file created successfully")
    return file_path


class TestExcelProcessor:
    """Tests for the ExcelProcessor class."""

    def test_initialization_default(
        self, excel_processor: ExcelProcessor, caplog: LogCaptureFixture
    ):
        """Test processor initialization with default settings.

        Args:
            excel_processor: Default processor instance
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing default ExcelProcessor initialization")

        logger.debug("Verifying default settings")
        assert excel_processor.max_rows is None
        assert excel_processor.skip_sheets == set()
        assert excel_processor.required_columns == set()
        logger.debug("Default settings verified successfully")

    def test_initialization_configured(
        self, configured_processor: ExcelProcessor, caplog: LogCaptureFixture
    ):
        """Test processor initialization with custom configuration.

        Args:
            configured_processor: Configured processor instance
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing configured ExcelProcessor initialization")

        logger.debug("Verifying configured settings")
        assert configured_processor.max_rows == 100
        assert configured_processor.skip_sheets == {"Internal"}
        assert configured_processor.required_columns == {"ID", "Name"}
        logger.debug("Configured settings verified successfully")

    def test_can_process_excel(
        self, excel_processor: ExcelProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test file type detection for Excel files.

        Args:
            excel_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing Excel file type detection")

        for ext in [".xlsx", ".xls"]:
            file_path = tmp_path / f"test{ext}"
            logger.debug("Testing extension: %s with path: %s", ext, file_path)
            assert excel_processor.can_process(file_path)

        logger.debug("Excel file type detection tests passed")

    def test_can_process_csv(
        self, excel_processor: ExcelProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test file type detection for CSV files.

        Args:
            excel_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing CSV file type detection")

        file_path = tmp_path / "test.csv"
        logger.debug("Testing CSV file: %s", file_path)
        assert excel_processor.can_process(file_path)
        logger.debug("CSV file type detection test passed")

    def test_can_process_unsupported(
        self, excel_processor: ExcelProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test file type detection for unsupported files.

        Args:
            excel_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing unsupported file type detection")

        file_path = tmp_path / "test.txt"
        logger.debug("Testing unsupported file: %s", file_path)
        assert not excel_processor.can_process(file_path)
        logger.debug("Unsupported file type detection test passed")

    def test_process_excel_success(
        self, excel_processor: ExcelProcessor, excel_file: Path, caplog: LogCaptureFixture
    ):
        """Test successful processing of Excel file.

        Args:
            excel_processor: Default processor instance
            excel_file: Test Excel file path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing successful Excel file processing")

        logger.debug("Processing Excel file: %s", excel_file)
        result = excel_processor.process(excel_file)

        logger.debug("Verifying processing result")
        assert result.status == "success"
        assert "sheets" in result.content
        assert "metadata" in result.content
        assert "Sheet1" in result.content["sheets"]
        assert "Sheet2" in result.content["sheets"]

        sheet1_data = result.content["sheets"]["Sheet1"]
        logger.debug("Verifying Sheet1 data structure")
        assert isinstance(sheet1_data, dict)
        assert "data" in sheet1_data
        assert "stats" in sheet1_data
        assert len(sheet1_data["data"]) == 3
        logger.debug("Excel processing test passed successfully")

    def test_process_csv_success(
        self, excel_processor: ExcelProcessor, csv_file: Path, caplog: LogCaptureFixture
    ):
        """Test successful processing of CSV file.

        Args:
            excel_processor: Default processor instance
            csv_file: Test CSV file path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing successful CSV file processing")

        logger.debug("Processing CSV file: %s", csv_file)
        result = excel_processor.process(csv_file)

        logger.debug("Verifying processing result")
        assert result.status == "success"
        assert "sheets" in result.content
        assert "metadata" in result.content
        assert "Sheet1" in result.content["sheets"]

        sheet_data = result.content["sheets"]["Sheet1"]
        logger.debug("Verifying CSV data structure")
        assert isinstance(sheet_data, dict)
        assert "data" in sheet_data
        assert "stats" in sheet_data
        assert len(sheet_data["data"]) == 3
        logger.debug("CSV processing test passed successfully")

    def test_skip_sheets(
        self,
        configured_processor: ExcelProcessor,
        tmp_path: Path,
        sample_df: pd.DataFrame,
        caplog: LogCaptureFixture,
    ):
        """Test skipping specified sheets.

        Args:
            configured_processor: Configured processor instance
            tmp_path: Temporary directory path
            sample_df: Sample DataFrame
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing sheet skipping functionality")

        file_path = tmp_path / "test.xlsx"
        logger.debug("Creating test file with multiple sheets: %s", file_path)
        with pd.ExcelWriter(file_path) as writer:
            sample_df.to_excel(writer, sheet_name="Sheet1", index=False)
            sample_df.to_excel(writer, sheet_name="Internal", index=False)

        logger.debug("Processing file with skip_sheets configuration")
        result = configured_processor.process(file_path)

        logger.debug("Verifying skipped sheets")
        assert "Internal" not in result.content["sheets"]
        assert "Sheet1" in result.content["sheets"]
        logger.debug("Sheet skipping test passed successfully")

    def test_max_rows_limit(
        self, tmp_path: Path, sample_df: pd.DataFrame, caplog: LogCaptureFixture
    ):
        """Test maximum rows limit.

        Args:
            tmp_path: Temporary directory path
            sample_df: Sample DataFrame
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing max rows limit")

        processor = ExcelProcessor({"max_rows": 2})
        logger.debug("Created processor with max_rows=2")

        file_path = tmp_path / "test.xlsx"
        logger.debug("Creating test file: %s", file_path)
        with pd.ExcelWriter(file_path) as writer:
            sample_df.to_excel(writer, sheet_name="Sheet1", index=False)

        logger.debug("Processing file with row limit")
        result = processor.process(file_path)

        logger.debug("Verifying row limit enforcement")
        assert len(result.content["sheets"]["Sheet1"]["data"]) == 2
        logger.debug("Row limit test passed successfully")

    def test_required_columns_present(
        self, tmp_path: Path, sample_df: pd.DataFrame, caplog: LogCaptureFixture
    ):
        """Test processing with required columns present.

        Args:
            tmp_path: Temporary directory path
            sample_df: Sample DataFrame
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing required columns validation - present")

        processor = ExcelProcessor({"required_columns": ["ID", "Name"]})
        logger.debug("Created processor with required columns: ID, Name")

        file_path = tmp_path / "test.xlsx"
        logger.debug("Creating test file: %s", file_path)
        with pd.ExcelWriter(file_path) as writer:
            sample_df.to_excel(writer, sheet_name="Sheet1", index=False)

        logger.debug("Processing file with required columns")
        result = processor.process(file_path)

        logger.debug("Verifying successful processing")
        assert result.status == "success"
        logger.debug("Required columns test passed successfully")

    def test_required_columns_missing(self, tmp_path: Path, caplog: LogCaptureFixture):
        """Test processing with required columns missing.

        Args:
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing required columns validation - missing")

        processor = ExcelProcessor({"required_columns": ["Missing"]})
        logger.debug("Created processor with required column: Missing")

        df = pd.DataFrame({"Present": [1, 2, 3]})
        file_path = tmp_path / "test.xlsx"
        logger.debug("Creating test file without required column: %s", file_path)
        with pd.ExcelWriter(file_path) as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False)

        logger.debug("Processing file with missing required column")
        result = processor.process(file_path)

        logger.debug("Verifying error result")
        assert result.status == "error"
        assert "Missing required columns" in result.error
        logger.debug("Missing columns test passed successfully")

    def test_empty_file(self, tmp_path: Path, caplog: LogCaptureFixture):
        """Test processing empty file.

        Args:
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing empty file processing")

        processor = ExcelProcessor()
        file_path = tmp_path / "empty.xlsx"

        logger.debug("Creating empty Excel file: %s", file_path)
        pd.DataFrame().to_excel(file_path, index=False)

        logger.debug("Processing empty file")
        result = processor.process(file_path)

        logger.debug("Verifying error result")
        assert result.status == "error"
        assert "No valid sheets found" in result.error
        logger.debug("Empty file test passed successfully")

    def test_process_invalid_file(
        self, excel_processor: ExcelProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test processing invalid file.

        Args:
            excel_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing invalid file processing")

        file_path = tmp_path / "invalid.xlsx"
        logger.debug("Creating invalid Excel file: %s", file_path)
        file_path.write_text("Invalid content")

        logger.debug("Processing invalid file")
        result = excel_processor.process(file_path)

        logger.debug("Verifying error result")
        assert result.status == "error"
        assert result.error is not None
        logger.debug("Invalid file test passed successfully")
