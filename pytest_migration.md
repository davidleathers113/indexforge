Each file shown below (besides docstrings and comments) stays under **100 lines** of code, focusing on clarity and maintainability in line with **SOLID** principles.

---

## Directory Layout

```
pytest_migrator/
├── __init__.py
├── main.py                  # Main entry point for the migration script.
├── context.py               # Defines the MigrationContext class.
├── visitors/
│   ├── __init__.py          # Initializes the visitors package.
│   ├── base.py              # Abstract MigrationVisitor base class.
│   ├── fixture_docstring.py # FixtureDocstringVisitor class.
│   ├── usefixtures.py       # UsefixturesVisitor class.
│   ├── exception_group.py   # ExceptionGroupVisitor class.
│   ├── thread_exception.py  # ThreadExceptionVisitor class.
│   ├── tmpdir_migration.py  # TmpdirMigrationVisitor class.
│   ├── parametrize.py       # ParametrizeVisitor class (if needed).
├── migrators/
│   ├── __init__.py          # Initializes the migrators package.
│   ├── file_migrator.py     # TestFileMigrator class.
│   ├── conftest_migrator.py # ConftestMigrator class.
│   ├── suite_migrator.py    # TestSuiteMigrator class.
├── utils/
│   ├── __init__.py          # Initializes the utils package.
│   ├── logging.py           # Logger configuration function.
└── requirements.txt         # Dependencies for the script.
```

Below are the **contents** of each file.  
Remember to run `pip install astunparse` (for Python < 3.9) or ensure Python ≥ 3.9 for native `ast.unparse`.

---

### `pytest_migrator/__init__.py`

```python
"""
Pytest Migrator Package Initialization.
"""
# Typically empty or can contain package metadata.
```

---

### `pytest_migrator/main.py`

```python
#!/usr/bin/env python3
"""
Main entry point for the Pytest Migration Script.
"""

import argparse
import sys
from migrators.suite_migrator import TestSuiteMigrator

def main():
    """
    Parses command-line arguments and initiates the migration.
    """
    parser = argparse.ArgumentParser(description="Migrate test suite to Pytest 8.3.4.")
    parser.add_argument("root_dir", help="Root directory containing tests.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Perform a dry run without making changes.")
    args = parser.parse_args()

    migrator = TestSuiteMigrator(args.root_dir, args.dry_run)
    success = migrator.migrate()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

---

### `pytest_migrator/context.py`

```python
"""
Stores shared migration context and state.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

@dataclass
class MigrationContext:
    """
    Holds migration configuration and state.
    """
    root_dir: Path
    dry_run: bool = False
    modified_files: Set[Path] = field(default_factory=set)
```

---

### `pytest_migrator/visitors/__init__.py`

```python
"""
Initializes the visitors package.
"""

from .base import MigrationVisitor
from .fixture_docstring import FixtureDocstringVisitor
from .usefixtures import UsefixturesVisitor
from .exception_group import ExceptionGroupVisitor
from .thread_exception import ThreadExceptionVisitor
from .tmpdir_migration import TmpdirMigrationVisitor
from .parametrize import ParametrizeVisitor

__all__ = [
    "MigrationVisitor",
    "FixtureDocstringVisitor",
    "UsefixturesVisitor",
    "ExceptionGroupVisitor",
    "ThreadExceptionVisitor",
    "TmpdirMigrationVisitor",
    "ParametrizeVisitor"
]
```

---

### `pytest_migrator/visitors/base.py`

```python
"""
Defines the abstract MigrationVisitor class for AST transformations.
"""

import ast
from abc import ABC, abstractmethod

class MigrationVisitor(ABC):
    """
    Abstract base for AST-based migration visitors.
    """

    @abstractmethod
    def visit(self, tree: ast.AST) -> ast.AST:
        """
        Visit and potentially transform the AST tree.
        """
        pass
```

---

### `pytest_migrator/visitors/fixture_docstring.py`

```python
"""
Visitor for updating fixture docstrings to an explicit multiline format.
"""

import ast
from .base import MigrationVisitor

class FixtureDocstringVisitor(MigrationVisitor):
    """
    Ensures fixture docstrings follow a consistent multiline style.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and self._is_fixture(node):
                self._update_docstring(node)
        return tree

    def _is_fixture(self, node: ast.FunctionDef) -> bool:
        return any(
            isinstance(dec, ast.Call) and getattr(dec.func, 'id', '') == 'fixture'
            for dec in node.decorator_list
        )

    def _update_docstring(self, node: ast.FunctionDef):
        if not node.body:
            return
        new_doc = '"""\nFixture: {}\n"""'.format(node.name)
        if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body[0].value.s = new_doc
        else:
            node.body.insert(0, ast.Expr(value=ast.Str(new_doc)))
```

---

### `pytest_migrator/visitors/usefixtures.py`

```python
"""
Visitor for removing or fixing empty @pytest.mark.usefixtures() calls.
"""

import ast
from .base import MigrationVisitor

class UsefixturesVisitor(MigrationVisitor):
    """
    Removes empty usefixtures markers in AST.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        removals = []
        for node in ast.walk(tree):
            if self._is_empty_usefixtures(node):
                removals.append(node)
        for node in removals:
            self._remove_from_decorators(tree, node)
        return tree

    def _is_empty_usefixtures(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if not (hasattr(func, 'attr') and hasattr(func, 'value')):
            return False
        if func.attr != 'usefixtures' or getattr(func.value, 'id', '') != 'pytest':
            return False
        return len(node.args) == 0

    def _remove_from_decorators(self, tree: ast.AST, target: ast.AST):
        for obj in ast.walk(tree):
            if isinstance(obj, ast.FunctionDef) and target in obj.decorator_list:
                obj.decorator_list.remove(target)
```

---

### `pytest_migrator/visitors/exception_group.py`

```python
"""
Visitor for converting 'except ExceptionGroup' to 'except* ExceptionGroup'.
"""

import ast
from .base import MigrationVisitor

class ExceptionGroupVisitor(MigrationVisitor):
    """
    Replaces 'except ExceptionGroup' blocks with 'except* ExceptionGroup'.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and self._is_exception_group(node):
                node.type = ast.Starred(
                    value=ast.Name(id="ExceptionGroup", ctx=ast.Load()),
                    ctx=ast.Load()
                )
        return tree

    def _is_exception_group(self, handler: ast.ExceptHandler) -> bool:
        return (handler.type and
                isinstance(handler.type, ast.Name) and
                handler.type.id == "ExceptionGroup")
```

---

### `pytest_migrator/visitors/thread_exception.py`

```python
"""
Visitor for adding tracemalloc import when 'threading' is used in fixtures.
"""

import ast
from .base import MigrationVisitor

class ThreadExceptionVisitor(MigrationVisitor):
    """
    Ensures tracemalloc import if 'threading' is imported.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        if self._threading_used(tree):
            self._ensure_tracemalloc_import(tree)
        return tree

    def _threading_used(self, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name == "threading":
                        return True
        return False

    def _ensure_tracemalloc_import(self, tree: ast.AST):
        if not self._has_tracemalloc(tree):
            imp = ast.Import(names=[ast.alias(name="tracemalloc", asname=None)])
            tree.body.insert(0, imp)

    def _has_tracemalloc(self, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name == "tracemalloc":
                        return True
        return False
```

---

### `pytest_migrator/visitors/tmpdir_migration.py`

```python
"""
Visitor for migrating 'tmpdir' usage to 'tmp_path'.
"""

import ast
from .base import MigrationVisitor

class TmpdirMigrationVisitor(MigrationVisitor):
    """
    Replaces 'tmpdir' references in the AST with 'tmp_path'.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "tmpdir":
                node.id = "tmp_path"
        return tree
```

---

### `pytest_migrator/visitors/parametrize.py`

```python
"""
Visitor for fixing empty parametrize calls.
"""

import ast
from .base import MigrationVisitor

class ParametrizeVisitor(MigrationVisitor):
    """
    Ensures @pytest.mark.parametrize isn't empty.
    """

    def visit(self, tree: ast.AST) -> ast.AST:
        for node in ast.walk(tree):
            if self._is_parametrize(node):
                self._fix_empty_parametrize(node)
        return tree

    def _is_parametrize(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        return (hasattr(func, 'attr') and func.attr == 'parametrize' and
                hasattr(func, 'value') and getattr(func.value, 'id', '') == 'pytest')

    def _fix_empty_parametrize(self, node: ast.Call):
        if len(node.args) == 2:
            if isinstance(node.args[1], ast.List) and not node.args[1].elts:
                node.args[1].elts.append(ast.Constant(value=None))
```

---

### `pytest_migrator/migrators/__init__.py`

```python
"""
Initializes the migrators package.
"""
```

---

### `pytest_migrator/migrators/file_migrator.py`

```python
"""
Handles migration of individual .py files by applying all visitors in sequence.
"""

import ast
import logging
from pathlib import Path
from ..context import MigrationContext
from ..visitors import (
    FixtureDocstringVisitor, UsefixturesVisitor, ExceptionGroupVisitor,
    ThreadExceptionVisitor, TmpdirMigrationVisitor, ParametrizeVisitor
)

class TestFileMigrator:
    """
    Applies all AST-based visitors to a single file.
    """

    def __init__(self, context: MigrationContext):
        self.context = context
        self.visitors = [
            FixtureDocstringVisitor(),
            UsefixturesVisitor(),
            ExceptionGroupVisitor(),
            ThreadExceptionVisitor(),
            TmpdirMigrationVisitor(),
            ParametrizeVisitor()
        ]

    def migrate_file(self, file_path: Path) -> bool:
        try:
            original_code = file_path.read_text()
            tree = ast.parse(original_code)
            for visitor in self.visitors:
                tree = visitor.visit(tree)
            new_code = ast.unparse(tree)
            if new_code != original_code and not self.context.dry_run:
                file_path.write_text(new_code)
                self.context.modified_files.add(file_path)
                logging.info(f"Migrated {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to migrate {file_path}: {e}")
            return False
```

---

### `pytest_migrator/migrators/conftest_migrator.py`

```python
"""
Adds tracemalloc hooks to conftest.py if missing.
"""

import logging
from pathlib import Path
from ..context import MigrationContext

class ConftestMigrator:
    """
    Manages conftest.py updates for tracemalloc.
    """

    HOOKS = """
import tracemalloc

def pytest_configure(config):
    tracemalloc.start()

def pytest_unconfigure(config):
    tracemalloc.stop()
"""

    def __init__(self, context: MigrationContext):
        self.context = context

    def migrate_conftest(self, file_path: Path) -> bool:
        try:
            text = file_path.read_text()
            if "pytest_configure" not in text and not self.context.dry_run:
                with open(file_path, "a") as f:
                    f.write(self.HOOKS)
                self.context.modified_files.add(file_path)
                logging.info(f"Added tracemalloc hooks to {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to migrate conftest {file_path}: {e}")
            return False
```

---

### `pytest_migrator/migrators/suite_migrator.py`

```python
"""
Orchestrates migration of the entire test suite.
"""

import logging
from pathlib import Path
from ..context import MigrationContext
from .file_migrator import TestFileMigrator
from .conftest_migrator import ConftestMigrator

class TestSuiteMigrator:
    """
    Coordinates conftest.py and .py file migration.
    """

    def __init__(self, root_dir: str, dry_run: bool):
        self.context = MigrationContext(Path(root_dir), dry_run)
        self.file_migrator = TestFileMigrator(self.context)
        self.conftest_migrator = ConftestMigrator(self.context)

    def migrate(self) -> bool:
        try:
            for conftest in self.context.root_dir.rglob("conftest.py"):
                self.conftest_migrator.migrate_conftest(conftest)
            for py_file in self.context.root_dir.rglob("*.py"):
                if py_file.name != "conftest.py":
                    self.file_migrator.migrate_file(py_file)
            logging.info(f"Migration complete. Modified {len(self.context.modified_files)} files.")
            return True
        except Exception as e:
            logging.error(f"Migration failed: {e}")
            return False
```

---

### `pytest_migrator/utils/__init__.py`

```python
"""
Utility package initializer.
"""
```

---

### `pytest_migrator/utils/logging.py`

```python
"""
Sets up logging for the migration process.
"""

import logging
import sys

def configure_logging(log_file="pytest_migration.log"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

---

### `pytest_migrator/requirements.txt`

```
# Required packages for AST unparse on Python < 3.9
astunparse

# Or ensure Python 3.9+ to use built-in ast.unparse
```

---

## Usage and Verification

1. **Install Dependencies** (if using Python < 3.9):

   ```bash
   pip install astunparse
   ```

   Or confirm you’re on Python 3.9+:

   ```bash
   python --version
   ```

2. **Run the Script**:

   ```bash
   python -m pytest_migrator.main /path/to/tests
   ```

   Use `--dry-run` if you want to see what would change without writing updates:

   ```bash
   python -m pytest_migrator.main /path/to/tests --dry-run
   ```

3. **Check Logs**:

   - By default, logs appear in `pytest_migration.log` (if you configure logging with `utils/logging.py`).
   - Also streamed to STDOUT.

4. **Run Pytest**:

   - Ensure you have Pytest 8.3.4 installed:
     ```bash
     pip install --upgrade pytest==8.3.4
     ```
   - Validate by running:
     ```bash
     pytest --version
     ```
   - Finally, run your test suite:
     ```bash
     pytest
     ```
   - Confirm the tests pass without warnings or errors.

5. **Compare with Source Control**:
   - If you use Git, review the changes:
     ```bash
     git diff
     ```
   - Verify no unwanted replacements or transformations occurred.
