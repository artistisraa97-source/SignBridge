# Common utilities

import os

def get_static_file_path(filename: str) -> str:
    """Get path for static files."""
    return os.path.join('.', filename)

def ensure_dir(path: str):
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)