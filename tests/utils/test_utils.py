"""Generic test utilities."""
from contextlib import contextmanager
import os
from pathlib import Path
import random
import string
import tempfile
from typing import Generator, Optional, Union
import uuid

__all__ = ['create_temp_file', 'create_temp_dir', 'cleanup_files', 'generate_random_string', 'generate_uuid', 'freeze_time', 'advance_time']

def create_temp_file(content: str='', suffix: str='.txt') -> Path:
    """Create a temporary file with given content and suffix."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return Path(path)
    except *Exception:
        cleanup_files(Path(path))
        raise

def create_temp_dir() -> Path:
    """Create a temporary directory."""
    return Path(tempfile.mkdtemp())

def cleanup_files(*paths: Union[str, Path]) -> None:
    """Clean up files and directories."""
    for path in paths:
        path = Path(path)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)

def generate_random_string(length: int=10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits
    return ''.join((random.choice(letters) for _ in range(length)))

def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())

@contextmanager
def freeze_time(timestamp: Optional[float]=None) -> Generator[float, None, None]:
    """Freeze time at a specific timestamp."""
    import time
    real_time = time.time
    frozen_time = timestamp or real_time()
    time.time = lambda: frozen_time
    try:
        yield frozen_time
    finally:
        time.time = real_time

def advance_time(seconds: float=1.0) -> None:
    """Advance the current time by specified seconds."""
    import time
    current_time = time.time()
    time.time = lambda: current_time + seconds