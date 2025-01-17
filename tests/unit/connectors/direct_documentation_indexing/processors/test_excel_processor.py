"""Tests for the ExcelProcessor class."""

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest

from src.core.processors.base import ProcessingResult
from src.core.processors.excel import ExcelProcessor


@pytest.fixture
def processor(caplog):
    """Fixture for creating an Excel processor instance."""
    caplog.set_level(logging.DEBUG)
    config = {"max_rows": 1000}
    return ExcelProcessor(config=config)


@pytest.fixture
def excel_file(tmp_path) -> Path:
    """Fixture for creating a test Excel file."""
    file_path = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_file(tmp_path) -> Path:
    """Fixture for creating a test CSV file."""
    file_path = tmp_path / "test.csv"
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    df.to_csv(file_path, index=False)
    return file_path


def test_initialization(processor, caplog):
    """Test Excel processor initialization."""
    assert isinstance(processor, ExcelProcessor)
    assert processor.logger is not None
    assert processor.max_rows == 1000
    assert "Excel processor initialized with max_rows=1000" in caplog.text


def test_can_process_excel(processor, excel_file):
    """Test Excel file processing capability."""
    assert processor.can_process(excel_file) is True
    assert not processor.can_process(Path("test.txt"))


def test_can_process_csv(processor, csv_file):
    """Test CSV file processing capability."""
    assert processor.can_process(csv_file) is True


def test_process_excel_success(processor, excel_file, caplog):
    """Test successful Excel file processing."""
    result = processor.process(excel_file)
    assert isinstance(result, ProcessingResult)
    assert result.status == "success"
    assert isinstance(result.content, List)
    assert len(result.content) == 1  # One sheet
    assert isinstance(result.content[0], Dict)
    assert "sheet_name" in result.content[0]
    assert "data" in result.content[0]
    assert "Processing Excel file" in caplog.text


def test_process_csv_success(processor, csv_file, caplog):
    """Test successful CSV file processing."""
    result = processor.process(csv_file)
    assert isinstance(result, ProcessingResult)
    assert result.status == "success"
    assert isinstance(result.content, List)
    assert len(result.content) == 1
    assert isinstance(result.content[0], Dict)
    assert "Processing CSV file" in caplog.text


def test_process_invalid_file(processor):
    """Test processing an invalid file."""
    with pytest.raises(OSError, match="File not found"):
        processor.process(Path("nonexistent.xlsx"))


def test_process_empty_excel(processor, tmp_path):
    """Test processing an empty Excel file."""
    file_path = tmp_path / "empty.xlsx"
    pd.DataFrame().to_excel(file_path, index=False)
    result = processor.process(file_path)
    assert result.status == "success"
    assert len(result.content) == 1
    assert len(result.content[0]["data"]) == 0


def test_process_multiple_sheets(processor, tmp_path):
    """Test processing Excel file with multiple sheets."""
    file_path = tmp_path / "multi_sheet.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        pd.DataFrame({"A": [1]}).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame({"B": [2]}).to_excel(writer, sheet_name="Sheet2", index=False)

    result = processor.process(file_path)
    assert result.status == "success"
    assert len(result.content) == 2
    assert result.content[0]["sheet_name"] != result.content[1]["sheet_name"]


def test_max_rows_limit(processor, tmp_path):
    """Test max rows limit enforcement."""
    file_path = tmp_path / "large.xlsx"
    df = pd.DataFrame({"A": range(2000)})
    df.to_excel(file_path, index=False)

    result = processor.process(file_path)
    assert result.status == "success"
    assert len(result.content[0]["data"]) == 1000  # Max rows limit


def test_custom_max_rows(caplog):
    """Test custom max rows configuration."""
    config = {"max_rows": 500}
    custom_processor = ExcelProcessor(config=config)
    assert custom_processor.max_rows == 500
    assert "Excel processor initialized with max_rows=500" in caplog.text
