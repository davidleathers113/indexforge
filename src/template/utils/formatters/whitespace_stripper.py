"""Whitespace stripper formatter."""

from .base_formatter import BaseFormatter


class WhitespaceStripper(BaseFormatter):
    """Strips trailing whitespace from lines."""

    def format(self, content: str) -> str:
        """Strip trailing whitespace from all lines.

        Args:
            content: Content to process

        Returns:
            str: Content with trailing whitespace removed
        """
        lines = content.split("\n")
        return "\n".join(line.rstrip() for line in lines)
