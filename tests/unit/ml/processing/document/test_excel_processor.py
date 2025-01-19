"""Unit tests for Excel document processor.

Tests the functionality of Excel document processing, including sheet handling,
data extraction, and configuration validation.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.ml.processing.document.config import DocumentProcessingConfig, ExcelProcessingConfig
from src.ml.processing.document.errors import DocumentProcessingError, DocumentValidationError
from src.ml.processing.document.excel import ExcelProcessor


@pytest.fixture
def sample_data():
    """Create sample Excel data for testing."""
    return {
        "Sheet1": pd.DataFrame({"ID": [1, 2, 3], "Name": ["A", "B", "C"], "Value": [10, 20, 30]}),
        "Sheet2": pd.DataFrame({"Category": ["X", "Y", "Z"], "Count": [5, 15, 25]}),
    }


@pytest.fixture
def processor():
    """Create a test processor instance."""
    return ExcelProcessor()


@pytest.fixture
def config():
    """Create a test configuration."""
    return DocumentProcessingConfig(
        excel_config=ExcelProcessingConfig(
            max_rows=1000,
            max_cols=50,
            sheet_names={"Sheet1"},
            header_row=0,
            skip_empty=True,
            required_columns=["ID", "Name"],
        )
    )


def test_processor_initialization(processor):
    """Test processor initialization."""
    assert not processor.is_initialized
    processor.initialize()
    assert processor.is_initialized
    assert not processor._processed_sheets
    processor.cleanup()
    assert not processor.is_initialized


def test_process_csv_file(processor, tmp_path):
    """Test processing CSV file."""
    # Create test CSV
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)

    processor.initialize()
    result = processor.process(csv_path)
    processor.cleanup()

    assert result.status == "success"
    assert "Sheet1" in result.content["data"]
    assert_frame_equal(result.content["data"]["Sheet1"], df)


def test_process_excel_file(processor, tmp_path, sample_data):
    """Test processing Excel file."""
    # Create test Excel file
    excel_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        for sheet_name, df in sample_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "success"
    assert set(result.content["data"].keys()) == set(sample_data.keys())
    for sheet_name in sample_data:
        assert_frame_equal(result.content["data"][sheet_name], sample_data[sheet_name])


def test_sheet_filtering(processor, tmp_path, sample_data):
    """Test sheet filtering based on configuration."""
    excel_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        for sheet_name, df in sample_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    processor.config.excel_config.sheet_names = {"Sheet1"}
    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "success"
    assert set(result.content["data"].keys()) == {"Sheet1"}
    assert_frame_equal(result.content["data"]["Sheet1"], sample_data["Sheet1"])


def test_row_limit(processor, tmp_path):
    """Test row limit enforcement."""
    df = pd.DataFrame({"A": range(10), "B": range(10)})
    excel_path = tmp_path / "test.xlsx"
    df.to_excel(excel_path, index=False)

    processor.config.excel_config.max_rows = 5
    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "success"
    assert len(result.content["data"]["Sheet1"]) == 5


def test_column_limit(processor, tmp_path):
    """Test column limit enforcement."""
    df = pd.DataFrame({f"Col{i}": range(5) for i in range(10)})
    excel_path = tmp_path / "test.xlsx"
    df.to_excel(excel_path, index=False)

    processor.config.excel_config.max_cols = 3
    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "success"
    assert len(result.content["data"]["Sheet1"].columns) == 3


def test_required_columns(processor, tmp_path):
    """Test required columns validation."""
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    excel_path = tmp_path / "test.xlsx"
    df.to_excel(excel_path, index=False)

    processor.config.excel_config.required_columns = ["C"]
    processor.initialize()
    with pytest.raises(DocumentValidationError):
        processor.process(excel_path)
    processor.cleanup()


def test_skip_empty_rows(processor, tmp_path):
    """Test empty row handling."""
    df = pd.DataFrame(
        {
            "A": [1, None, 3],
            "B": [None, None, None],
        }
    )
    excel_path = tmp_path / "test.xlsx"
    df.to_excel(excel_path, index=False)

    processor.config.excel_config.skip_empty = True
    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "success"
    assert len(result.content["data"]["Sheet1"]) < len(df)


def test_metadata_tracking(processor, tmp_path, sample_data):
    """Test metadata tracking during processing."""
    excel_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        for sheet_name, df in sample_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    processor.initialize()
    result = processor.process(excel_path)
    metadata = processor.get_metadata()
    processor.cleanup()

    assert result.status == "success"
    assert "processed_files" in metadata
    assert "last_file" in metadata
    assert metadata["processed_files"] == 1


def test_error_handling(processor, tmp_path):
    """Test error handling during processing."""
    non_excel_file = tmp_path / "test.txt"
    non_excel_file.touch()

    processor.initialize()
    with pytest.raises(DocumentProcessingError):
        processor.process(non_excel_file)
    processor.cleanup()


def test_invalid_sheet_names(processor, tmp_path, sample_data):
    """Test handling of invalid sheet names in configuration."""
    excel_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        for sheet_name, df in sample_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    processor.config.excel_config.sheet_names = {"NonexistentSheet"}
    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "error"
    assert any("Specified sheets not found" in error for error in result.errors)


def test_file_access_error(processor, tmp_path):
    """Test handling of file access errors."""
    excel_path = tmp_path / "test.xlsx"
    excel_path.touch()
    excel_path.chmod(0o000)  # Remove all permissions

    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "error"
    assert any("Permission denied" in error for error in result.errors)

    # Restore permissions for cleanup
    excel_path.chmod(0o666)


def test_corrupted_file(processor, tmp_path):
    """Test handling of corrupted Excel files."""
    excel_path = tmp_path / "test.xlsx"
    with open(excel_path, "wb") as f:
        f.write(b"Not a valid Excel file")

    processor.initialize()
    result = processor.process(excel_path)
    processor.cleanup()

    assert result.status == "error"
    assert len(result.errors) > 0
