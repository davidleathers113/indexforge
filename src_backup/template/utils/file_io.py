"""File I/O operations for code cleanup utility."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class FileIO:
    """Handles all file I/O operations."""

    def read_file(self, filepath: str | Path) -> str:
        """Read content from a file.

        Args:
            filepath: Path to the file to read

        Returns:
            str: Content of the file

        Raises:
            IOError: If file cannot be read
        """
        path = Path(filepath)
        logger.debug("Reading file: %s", path)

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            logger.debug("Successfully read %s", path)
            return content
        except Exception as e:
            logger.error("Failed to read %s: %s", path, str(e))
            raise OSError(f"Failed to read {path}: {e!s}")

    def write_file(self, filepath: str | Path, content: str) -> None:
        """Write content to a file.

        Args:
            filepath: Path to the file to write
            content: Content to write to the file

        Raises:
            IOError: If file cannot be written
        """
        path = Path(filepath)
        logger.debug("Writing to file: %s", path)

        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            logger.debug("Successfully wrote to %s", path)
        except Exception as e:
            logger.error("Failed to write to %s: %s", path, str(e))
            raise OSError(f"Failed to write to {path}: {e!s}")

    def read_binary_file(self, filepath: str | Path) -> bytes:
        """Read binary content from a file.

        Args:
            filepath: Path to the file to read

        Returns:
            bytes: Binary content of the file

        Raises:
            IOError: If file cannot be read
        """
        path = Path(filepath)
        logger.debug("Reading binary file: %s", path)

        try:
            with open(path, "rb") as f:
                content = f.read()
            logger.debug("Successfully read binary file %s", path)
            return content
        except Exception as e:
            logger.error("Failed to read binary file %s: %s", path, str(e))
            raise OSError(f"Failed to read binary file {path}: {e!s}")
