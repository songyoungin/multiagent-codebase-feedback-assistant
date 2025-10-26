"""Dependency checker tool for analyzing unused dependencies."""

import ast
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from common.logger import get_logger
from common.schemas import DEFAULT_EXCLUDE_PATTERNS, DependencyCheckResult

logger = get_logger(__name__)


def check_unused_dependencies(
    project_path: str,
    exclude_patterns: Optional[list[str]] = None,  # noqa: UP045 (incompatible with google-adk function parsing)
) -> dict[str, Any]:
    """Check for unused dependencies in the project.

    Args:
        project_path: Root path to analyze
        exclude_patterns: List of patterns to exclude from analysis (optional)

    Returns:
        Dictionary representation of DependencyCheckResult object
    """
    logger.info(f"Starting dependency check at: {project_path}")

    # Always merge with default exclude patterns
    exclude_patterns = list(set(DEFAULT_EXCLUDE_PATTERNS) | set(exclude_patterns or []))

    # Validate path
    root = Path(project_path)
    if not root.exists():
        logger.error(f"Path does not exist: {project_path}")
        raise FileNotFoundError(f"Path does not exist: {project_path}")

    if not root.is_dir():
        logger.error(f"Path is not a directory: {project_path}")
        raise NotADirectoryError(f"Path is not a directory: {project_path}")

    # Parse declared dependencies
    declared = _parse_declared_dependencies(root)
    logger.info(f"Found {len(declared)} declared dependencies")

    # Extract used imports
    used = _extract_used_imports(root, exclude_patterns)
    logger.info(f"Found {len(used)} used dependencies")

    # Calculate unused dependencies using venv metadata
    unused, packages_without_metadata = _calculate_unused_dependencies(declared, used, root)

    logger.info(f"Identified {len(unused)} unused dependencies: {sorted(unused)}")
    logger.info(
        f"Found {len(packages_without_metadata)} packages without metadata: {sorted(packages_without_metadata)}"
    )

    # Create DependencyCheckResult and return as dictionary
    result = DependencyCheckResult(
        project_path=project_path,
        declared_dependencies=sorted(declared),
        used_dependencies=sorted(used),
        unused_dependencies=sorted(unused),
        packages_without_metadata=sorted(packages_without_metadata),
        checked_at=datetime.now(),
    ).model_dump()

    return result


def _calculate_unused_dependencies(
    declared: set[str], used: set[str], project_root: Path
) -> tuple[set[str], list[str]]:
    """Calculate unused dependencies using venv metadata.

    Args:
        declared: Set of declared package names
        used: Set of used import names
        project_root: Project root directory (to find venv)

    Returns:
        Tuple of (unused packages with metadata, packages without metadata)
    """
    unused = set()
    packages_without_metadata = []

    for package in declared:
        venv_imports = _find_top_level_from_venv(package, project_root)

        if venv_imports:
            # Metadata found: directly check if used
            if not any(import_name in used for import_name in venv_imports):
                unused.add(package)
                logger.debug(f"Package '{package}' marked as unused (metadata check)")
        else:
            # No metadata: will be analyzed by agent
            packages_without_metadata.append(package)
            logger.debug(f"Package '{package}' has no metadata, agent will analyze")

    return unused, packages_without_metadata


def _find_top_level_from_venv(package_name: str, project_root: Path) -> set[str] | None:
    """Find top-level import names from project's virtual environment.

    Args:
        package_name: Package name (e.g., "google-adk")
        project_root: Project root directory

    Returns:
        Set of top-level import names, or None if not found
    """
    # Common virtual environment directory names
    venv_dirs = [".venv", "venv", ".env", "env"]

    for venv_name in venv_dirs:
        venv_path = project_root / venv_name
        if not venv_path.exists():
            continue

        # Find site-packages directory
        site_packages_paths = list(venv_path.glob(f"lib/python{sys.version_info.major}.*/site-packages"))
        if not site_packages_paths:
            # Try alternative structure (Windows)
            site_packages_paths = list(venv_path.glob("Lib/site-packages"))

        for site_packages in site_packages_paths:
            if not site_packages.exists():
                continue

            # Look for .dist-info directories
            # Package names can have different formats: google-adk, google_adk, etc.
            dist_info_patterns = [
                f"{package_name}-*.dist-info",
                f"{package_name.replace('-', '_')}-*.dist-info",
                f"{package_name.replace('_', '-')}-*.dist-info",
            ]

            for pattern in dist_info_patterns:
                dist_info_dirs = list(site_packages.glob(pattern))
                for dist_info_dir in dist_info_dirs:
                    top_level_file = dist_info_dir / "top_level.txt"
                    if top_level_file.exists():
                        try:
                            content = top_level_file.read_text(encoding="utf-8").strip()
                            if content:
                                imports = {line.strip() for line in content.split("\n") if line.strip()}
                                return imports
                        except Exception as e:
                            logger.warning(f"Error reading {top_level_file}: {e}")

    return None


def _parse_declared_dependencies(project_root: Path) -> set[str]:
    """Parse declared dependencies from pyproject.toml.

    Args:
        project_root: Project root directory

    Returns:
        Set of declared dependency package names
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        logger.warning(f"pyproject.toml not found at {pyproject_path}")
        return set()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        dependencies = data.get("project", {}).get("dependencies", [])

        # Extract package names (remove version specifiers and extras)
        # Example: "google-adk[a2a]>=1.17.0" -> "google-adk"
        # Example: "fastapi>=0.119.0" -> "fastapi"
        package_names = set()
        for dep in dependencies:
            # Remove extras first (e.g., [a2a])
            dep_without_extras = re.sub(r"\[.*?\]", "", dep)

            # Extract package name before version specifiers
            match = re.match(r"^([a-zA-Z0-9_-]+)", dep_without_extras)
            if match:
                # Keep original package name (with hyphens), only convert to lowercase
                package_name = match.group(1).lower()
                package_names.add(package_name)

        logger.info(f"Declared dependencies: {sorted(package_names)}")
        return package_names

    except Exception as e:
        logger.error(f"Error parsing pyproject.toml: {e}")
        return set()


def _extract_used_imports(project_root: Path, exclude_patterns: list[str]) -> set[str]:
    """Extract used imports from Python source files.

    Args:
        project_root: Project root directory
        exclude_patterns: Patterns to exclude

    Returns:
        Set of imported package names
    """
    imported_packages = set()

    # Find all Python files
    for py_file in project_root.rglob("*.py"):
        # Check exclude patterns
        if _should_exclude(py_file, project_root, exclude_patterns):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        package = _extract_top_level_package(alias.name)
                        if package and not _is_stdlib_module(package):
                            imported_packages.add(package)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        package = _extract_top_level_package(node.module)
                        if package and not _is_stdlib_module(package):
                            imported_packages.add(package)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Error processing {py_file}: {e}")

    logger.info(f"Used imports: {sorted(imported_packages)}")
    return imported_packages


def _extract_top_level_package(module_name: str) -> str:
    """Extract top-level package name from module path.

    Args:
        module_name: Full module name (e.g., "fastapi.responses")

    Returns:
        Top-level package name (e.g., "fastapi")
    """
    return module_name.split(".")[0]


def _is_stdlib_module(module_name: str) -> bool:
    """Check if module is part of Python standard library.

    Args:
        module_name: Module name to check

    Returns:
        True if module is in stdlib, False otherwise
    """
    # Use sys.stdlib_module_names (available in Python 3.10+)
    return module_name in sys.stdlib_module_names


def _should_exclude(file_path: Path, project_root: Path, exclude_patterns: list[str]) -> bool:
    """Check if file should be excluded from analysis.

    Args:
        file_path: File path to check
        project_root: Project root directory
        exclude_patterns: List of patterns to exclude

    Returns:
        True if excluded, False otherwise
    """
    try:
        relative_path = file_path.relative_to(project_root)
        path_str = str(relative_path)

        for pattern in exclude_patterns:
            # Check if any part of the path matches the pattern
            if pattern in path_str or path_str.startswith(pattern):
                return True

    except ValueError:
        # File is not relative to project root
        return True

    return False
