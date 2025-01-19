"""Python code cleanup utility.

This module provides utilities for cleaning up Python code files.
"""

import argparse
import logging
from pathlib import Path

from .config import Config
from .file_io import FileIO
from .formatters import (
    BlackFormatter,
    ImportSorter,
    IndentationFixer,
    MultipleStatementSplitter,
    WhitespaceStripper,
)
from .logging_config import setup_logging
from .processors import AIProcessor, FileProcessor, TemplateDetector


# Initialize logging
logger = setup_logging()


class CleanupOrchestrator:
    """Orchestrates the code cleanup process."""

    def __init__(self, config: Config):
        """Initialize the orchestrator with configuration."""
        self.config = config
        self.file_io = FileIO()
        self.template_detector = TemplateDetector()
        self.processors = {
            "whitespace": WhitespaceStripper(),
            "statements": MultipleStatementSplitter(),
            "indentation": IndentationFixer(config.PYTHON_INDENT),
            "imports": ImportSorter(config.ISORT_CONFIG),
            "black": BlackFormatter(config.BLACK_CONFIG),
            "ai": AIProcessor(config.OPENAI_CONFIG),
        }
        logger.debug(
            "Initialized CleanupOrchestrator with config: indent=%d, black_line_length=%d",
            config.PYTHON_INDENT,
            config.BLACK_CONFIG.line_length,
        )

    def process_file(self, filepath: str | Path, use_ai: bool = False) -> bool:
        """Process a single file with all cleanup operations."""
        try:
            path = Path(filepath)
            logger.info("Starting to process file: %s", filepath)

            if not path.exists():
                logger.error("File does not exist: %s", path)
                return False

            if not path.is_file():
                logger.error("Path is not a file: %s", path)
                return False

            # Read file and detect if it's a template
            try:
                content = self.file_io.read_file(path)
            except OSError as e:
                logger.error("Failed to read file %s: %s", path, str(e))
                return False

            is_template = self.template_detector.is_template_file(content)
            logger.debug("File %s is %sa template", path, "" if is_template else "not ")

            # Create processor with appropriate configuration
            processor = FileProcessor(self.processors, is_template=is_template, use_ai=use_ai)

            # Process the file
            result = processor.process(path, content)
            if result.success:
                try:
                    self.file_io.write_file(path, result.content)
                    logger.info("Successfully processed: %s", path)
                    return True
                except OSError as e:
                    logger.error("Failed to write processed content to %s: %s", path, str(e))
                    return False
            else:
                logger.error("Failed to process %s: %s", path, result.error)
                return False

        except Exception as e:
            logger.error("Unexpected error processing %s: %s", filepath, str(e), exc_info=True)
            return False

    def process_directory(
        self, directory_path: str | Path, use_ai: bool = False
    ) -> list[str]:
        """Process all Python files in a directory."""
        path = Path(directory_path)
        failed_files = []

        if not path.exists():
            logger.error("Directory does not exist: %s", path)
            return [str(path)]

        if not path.is_dir():
            logger.error("Path is not a directory: %s", path)
            return [str(path)]

        logger.info("Processing directory: %s", path)
        total_files = 0
        processed_files = 0

        try:
            python_files = list(path.glob("**/*.py"))
            total_files = len(python_files)
            logger.info("Found %d Python files to process", total_files)

            for python_file in python_files:
                if not self.process_file(python_file, use_ai):
                    failed_files.append(str(python_file))
                else:
                    processed_files += 1
                logger.debug(
                    "Progress: %d/%d files processed (%d failed)",
                    processed_files,
                    total_files,
                    len(failed_files),
                )

        except Exception as e:
            logger.error(
                "Unexpected error processing directory %s: %s", path, str(e), exc_info=True
            )
            return [str(path)]

        if failed_files:
            logger.warning(
                "Completed with %d failures out of %d files", len(failed_files), total_files
            )
        else:
            logger.info("Successfully processed all %d files", total_files)

        return failed_files


def main() -> None:
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(description="Clean up Python files.")
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI-powered improvements")
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Initialize orchestrator
    config = Config()
    orchestrator = CleanupOrchestrator(config)

    # Process path
    path = Path(args.path)
    if path.is_file():
        success = orchestrator.process_file(path, args.use_ai)
        exit(0 if success else 1)
    elif path.is_dir():
        failed = orchestrator.process_directory(path, args.use_ai)
        if failed:
            logger.error("Failed to process the following files:")
            for file in failed:
                logger.error("  %s", file)
            exit(1)
        exit(0)
    else:
        logger.error("Path does not exist: %s", path)
        exit(1)


if __name__ == "__main__":
    main()
