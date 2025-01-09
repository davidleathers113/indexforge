"""Script to update imports in test files to use the new cross_reference module."""

import os
import re


def update_imports(file_path):
    """Update imports in a file to use the new cross_reference module."""
    with open(file_path, "r") as f:
        content = f.read()

    # Replace imports from old location to new location
    content = re.sub(
        r"from src\.connectors\.direct_documentation_indexing\.source_tracking\.cross_references import \(",
        "from cross_reference import (",
        content,
    )

    with open(file_path, "w") as f:
        f.write(content)


def main():
    """Update imports in all test files."""
    test_dir = "tests/connectors/direct_documentation_indexing/source_tracking"
    for filename in os.listdir(test_dir):
        if filename.endswith(".py"):
            file_path = os.path.join(test_dir, filename)
            print(f"Updating {file_path}")
            update_imports(file_path)


if __name__ == "__main__":
    main()
