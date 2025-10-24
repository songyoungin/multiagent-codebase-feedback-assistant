"""Filesystem scan tool."""

import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Any

from common.logger import get_logger
from common.schemas import FileInfo, ProjectStructure, ScanRequest

logger = get_logger(__name__)


def scan_project(
    root_path: str,
    exclude_patterns: list[str] | None = None,
    max_depth: int | None = None,
) -> dict[str, Any]:
    """Scan the project structure.

    Args:
        root_path: Root path to scan
        exclude_patterns: List of patterns to exclude (e.g., [".git", "*.pyc"])
        max_depth: Maximum search depth (unlimited if None)

    Returns:
        Dictionary representation of ProjectStructure object
    """
    logger.info(f"Starting project scan at: {root_path}")

    # Apply default exclude patterns
    if exclude_patterns is None:
        exclude_patterns = ScanRequest().exclude_patterns

    # Validate path
    root = Path(root_path)
    if not root.exists():
        logger.error(f"Path does not exist: {root_path}")
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    if not root.is_dir():
        logger.error(f"Path is not a directory: {root_path}")
        raise NotADirectoryError(f"Path is not a directory: {root_path}")

    # Recursive scan
    files = _scan_directory_recursive(
        root, exclude_patterns, max_depth, current_depth=0
    )

    # Calculate statistics
    total_files = sum(1 for f in files if not f.is_directory)
    total_directories = sum(1 for f in files if f.is_directory)

    # Calculate file extension counts
    file_extensions: dict[str, int] = {}
    for file_info in files:
        if not file_info.is_directory and file_info.extension:
            ext = file_info.extension
            file_extensions[ext] = file_extensions.get(ext, 0) + 1

    logger.info(
        f"Scan completed: {total_files} files, {total_directories} directories, "
        f"{len(file_extensions)} unique extensions"
    )

    # Create ProjectStructure
    result = ProjectStructure(
        root_path=root_path,
        total_files=total_files,
        total_directories=total_directories,
        files=files,
        file_extensions=file_extensions,
        scanned_at=datetime.now(),
    )

    return result.model_dump()


def _scan_directory_recursive(
    path: Path,
    exclude_patterns: list[str],
    max_depth: int | None,
    current_depth: int,
) -> list[FileInfo]:
    """Recursively scan directories.

    Args:
        path: Path to scan
        exclude_patterns: List of patterns to exclude
        max_depth: Maximum search depth
        current_depth: Current depth

    Returns:
        List of FileInfo objects
    """
    # Check maximum depth
    if max_depth is not None and current_depth >= max_depth:
        return []

    results: list[FileInfo] = []

    try:
        for item in path.iterdir():
            # Check exclude patterns
            if _should_exclude(item, exclude_patterns):
                logger.debug(f"Excluding: {item}")
                continue

            # Create FileInfo
            try:
                stat = item.stat()
                file_info = FileInfo(
                    path=str(item),
                    size=stat.st_size if item.is_file() else 0,
                    extension=item.suffix if item.is_file() and item.suffix else None,
                    is_directory=item.is_dir(),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )
                results.append(file_info)

                # If directory, call recursively
                if item.is_dir():
                    sub_files = _scan_directory_recursive(
                        item, exclude_patterns, max_depth, current_depth + 1
                    )
                    results.extend(sub_files)

            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access {item}: {e}")
                continue

    except PermissionError as e:
        logger.warning(f"Permission denied for directory {path}: {e}")

    return results


def _should_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if file/directory matches exclude patterns.

    Args:
        path: Path to check
        exclude_patterns: List of patterns to exclude

    Returns:
        True if excluded, False otherwise
    """
    name = path.name
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False
