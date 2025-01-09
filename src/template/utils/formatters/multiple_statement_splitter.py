"""Multiple statement splitter formatter."""

import re

from .base_formatter import BaseFormatter


class MultipleStatementSplitter(BaseFormatter):
    """Splits multiple statements on a single line."""

    def format(self, content: str) -> str:
        """Split multiple statements into separate lines.

        Args:
            content: Content to process

        Returns:
            str: Content with statements split onto separate lines
        """
        lines = content.split("\n")
        result = []
        in_multiline_string = False
        string_quote = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append("")
                continue

            # Skip multiline strings
            if not in_multiline_string:
                if '"""' in stripped or "'''" in stripped:
                    quote = '"""' if '"""' in stripped else "'''"
                    if stripped.count(quote) == 1:
                        in_multiline_string = True
                        string_quote = quote
                        result.append(line)
                        continue
            else:
                if string_quote in stripped:
                    in_multiline_string = False
                    string_quote = None
                result.append(line)
                continue

            # Get the indentation of the current line
            indent = len(line) - len(stripped)
            current_indent = " " * indent

            # Handle function/class definitions with inline code
            if any(stripped.startswith(prefix) for prefix in ["def ", "class "]):
                if ":" in stripped:
                    colon_idx = stripped.index(":")
                    before_colon = stripped[: colon_idx + 1]
                    after_colon = stripped[colon_idx + 1 :]
                    result.append(current_indent + before_colon)
                    if after_colon.strip():
                        for stmt in self._split_statements(after_colon):
                            result.append(current_indent + "    " + stmt.strip())
                    continue

            # Handle semicolon-separated statements
            if ";" in stripped:
                statements = self._split_statements(stripped)
                for stmt in statements:
                    result.append(current_indent + stmt)
                continue

            # Handle multiple statements separated by whitespace
            if "    " in line:
                statements = self._split_statements(stripped)
                if len(statements) > 1:
                    for stmt in statements:
                        result.append(current_indent + stmt)
                    continue

            # Handle regular lines
            result.append(line)

        return "\n".join(result)

    def _split_statements(self, content: str) -> list:
        """Split content into individual statements.

        Args:
            content: Content to split

        Returns:
            list: List of statements
        """
        statements = []

        # First split by semicolons
        for stmt in content.split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue

            # Then split by multiple spaces (2 or more)
            parts = [p.strip() for p in re.split(r"\s{2,}|\t+", stmt) if p.strip()]
            statements.extend(parts)

        return statements
