"""Sentry utility functions.

This module provides utility functions for Sentry configuration and event processing.
"""

import os
import re
from typing import Optional


def get_git_commit() -> Optional[str]:
    """Get the current git commit hash."""
    try:
        with open(".git/HEAD") as f:
            ref = f.read().strip()
            if ref.startswith("ref: "):
                ref_path = os.path.join(".git", ref[5:])
                with open(ref_path) as f:
                    return f.read().strip()
            return ref
    except (FileNotFoundError, IOError):
        return None


def get_transaction_name(request) -> str:
    """Generate consistent transaction names.

    Args:
        request: FastAPI request object

    Returns:
        Formatted transaction name
    """
    path = request.url.path
    # Replace numeric IDs with {id} placeholder
    path = re.sub(r"/\d+", "/{id}", path)
    return f"{request.method} {path}"
