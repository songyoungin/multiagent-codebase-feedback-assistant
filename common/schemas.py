"""Data schema definitions."""

from datetime import datetime

from pydantic import BaseModel

# Default exclude patterns
DEFAULT_EXCLUDE_PATTERNS = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".*_cache",
    "*.pyc",
    ".DS_Store",
]


class FileInfo(BaseModel):
    """File information schema."""

    path: str
    size: int
    extension: str | None
    is_directory: bool
    modified_at: datetime | None = None


class ProjectStructure(BaseModel):
    """Project structure scan result schema."""

    root_path: str
    total_files: int
    total_directories: int
    files: list[FileInfo]
    file_extensions: dict[str, int]
    scanned_at: datetime


class ScanRequest(BaseModel):
    """Scan request schema."""

    root_path: str
    exclude_patterns: list[str] = DEFAULT_EXCLUDE_PATTERNS.copy()
    max_depth: int | None = None


class DependencyCheckResult(BaseModel):
    """Dependency check result schema."""

    project_path: str
    declared_dependencies: list[str]
    used_dependencies: list[str]
    unused_dependencies: list[str]
    packages_without_metadata: list[str]
    checked_at: datetime
