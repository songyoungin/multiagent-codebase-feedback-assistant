"""Data schema definitions."""

from datetime import datetime

from pydantic import BaseModel


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
    exclude_patterns: list[str] = [
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "*.pyc",
        ".DS_Store",
    ]
    max_depth: int | None = None
