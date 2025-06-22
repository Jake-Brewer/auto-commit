import fnmatch
from typing import List


def is_path_match(path: str, patterns: List[str]) -> bool:
    """Checks if a path matches any of the glob patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def should_process_path(path: str, include: List[str], exclude: List[str]) -> bool:
    """
    Determines if a file path should be processed based on include and
    exclude patterns. Exclude patterns take precedence over include patterns.
    """
    # Check for directory patterns in exclude
    for pattern in exclude:
        if pattern.endswith("/") and fnmatch.fnmatch(path + "/", pattern):
            return False

    if is_path_match(path, exclude):
        return False

    if is_path_match(path, include):
        return True

    return False
