"""Indentation fixer formatter."""

from .base_formatter import BaseFormatter


class IndentationFixer(BaseFormatter):
    """Formatter that fixes indentation in code."""

    def __init__(self, indent_size: int = 4):
        """Initialize with indentation size."""
        self.indent_size = indent_size

    def format(self, content: str) -> str:
        """Fix indentation in the content."""
        lines = content.splitlines()
        fixed_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append("")
                continue

            # Decrease indent for lines that start with dedent keywords
            if stripped.startswith(
                (
                    "return",
                    "break",
                    "continue",
                    "pass",
                    "raise",
                    "else:",
                    "elif ",
                    "except:",
                    "finally:",
                )
            ):
                indent_level = max(0, indent_level - 1)

            # Add the line with proper indentation
            fixed_lines.append(" " * (indent_level * self.indent_size) + stripped)

            # Increase indent after lines that end with colon
            if stripped.endswith(":"):
                indent_level += 1

        return "\n".join(fixed_lines)
