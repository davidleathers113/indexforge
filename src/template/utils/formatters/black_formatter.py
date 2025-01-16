"""Black code formatter."""

import logging

import black
from black import Mode, TargetVersion

from .base_formatter import BaseFormatter


logger = logging.getLogger(__name__)


class BlackFormatter(BaseFormatter):
    """Formats code using black."""

    def __init__(self, config):
        """Initialize with black configuration.

        Args:
            config: Black configuration settings
        """
        self.config = config

    def format(self, content: str) -> str:
        """Format content using black.

        Args:
            content: Content to format

        Returns:
            str: Formatted content
        """
        mode = Mode(
            target_versions={TargetVersion.PY37},
            line_length=self.config.line_length,
            string_normalization=True,
            is_pyi=False,
        )

        try:
            # First, normalize line endings
            content = content.replace("\r\n", "\n")

            # Remove trailing whitespace
            content = "\n".join(line.rstrip() for line in content.split("\n"))

            # Format with black
            formatted = black.format_str(content, mode=mode)

            # Ensure consistent line endings
            return formatted.rstrip() + "\n"
        except Exception as e:
            logger.error("Black formatting failed: %s", str(e))
            return content
