"""Data schema definitions."""

from datetime import datetime
from typing import Any, Literal

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


class MissingDocstring(BaseModel):
    """Missing docstring information schema."""

    item_type: str  # "class" or "function"
    name: str
    file_path: str
    line_number: int
    signature: str


class DocumentationAnalysisResult(BaseModel):
    """Documentation analysis result schema."""

    project_path: str
    files_analyzed: int
    total_items: int
    documented_items: int
    coverage_percentage: float
    missing_docstrings: list[MissingDocstring]
    analyzed_at: datetime


class CodeItem(BaseModel):
    """Code item (function or class) information schema."""

    item_type: Literal["class", "function"]
    name: str
    file_path: str
    line_number: int
    signature: str
    full_code: str
    parameters_count: int
    length_lines: int
    calls_functions: list[str]
    uses_imports: list[str]
    docstring: str | None = None


class SRPAnalysisResult(BaseModel):
    """SRP analysis result schema."""

    project_path: str
    files_analyzed: int
    total_items: int
    code_items: list[CodeItem]
    analyzed_at: datetime


class NamingItem(BaseModel):
    """Naming item (variable, function, class, parameter) information schema."""

    item_type: str  # "variable", "function", "class", "parameter"
    name: str
    file_path: str
    line_number: int
    context_code: str  # Signature or assignment
    type_hint: str | None = None
    docstring: str | None = None
    scope: str  # "local", "function", "method", "class", "parameter"


class NamingAnalysisResult(BaseModel):
    """Naming quality analysis result schema."""

    project_path: str
    files_analyzed: int
    total_items: int
    naming_items: list[NamingItem]
    analyzed_at: datetime


class OrchestrationResult(BaseModel):
    """Orchestration result schema."""

    project_path: str
    analyses_requested: list[str]
    analyses_completed: list[str]
    analyses_failed: list[str]
    results: dict[str, Any]
    errors: dict[str, str]
    analyzed_at: datetime
