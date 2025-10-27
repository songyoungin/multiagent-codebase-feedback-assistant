"""Documentation analyzer tool for finding missing docstrings."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from common.logger import get_logger
from common.schemas import DEFAULT_EXCLUDE_PATTERNS, DocumentationAnalysisResult, MissingDocstring

logger = get_logger(__name__)


def analyze_documentation(
    project_path: str,
    exclude_patterns: Optional[list[str]] = None,  # noqa: UP045 (incompatible with google-adk function parsing)
    include_private: bool = False,
) -> dict[str, Any]:
    """Analyze project documentation coverage.

    Args:
        project_path: Root path to analyze
        exclude_patterns: List of patterns to exclude from analysis (optional)
        include_private: Include private methods/functions (starting with _)

    Returns:
        Dictionary representation of DocumentationAnalysisResult object
    """
    logger.info(f"Starting documentation analysis at: {project_path}")

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

    # Analyze Python files
    missing_docstrings = []
    total_items = 0
    documented_items = 0
    files_analyzed = 0

    for py_file in root.rglob("*.py"):
        # Check exclude patterns
        if _should_exclude(py_file, root, exclude_patterns):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            file_missing, file_total, file_documented = _analyze_file(tree, py_file, root, include_private)

            missing_docstrings.extend(file_missing)
            total_items += file_total
            documented_items += file_documented
            files_analyzed += 1

        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Error processing {py_file}: {e}")

    # Calculate coverage
    coverage = (documented_items / total_items * 100) if total_items > 0 else 100.0

    logger.info(f"Analysis complete: {files_analyzed} files analyzed")
    logger.info(f"Documentation coverage: {coverage:.1f}% ({documented_items}/{total_items})")
    logger.info(f"Missing docstrings: {len(missing_docstrings)}")

    # Create result and return as dictionary
    result = DocumentationAnalysisResult(
        project_path=project_path,
        files_analyzed=files_analyzed,
        total_items=total_items,
        documented_items=documented_items,
        coverage_percentage=round(coverage, 2),
        missing_docstrings=missing_docstrings,
        analyzed_at=datetime.now(),
    ).model_dump()

    return result


def _analyze_file(
    tree: ast.AST, file_path: Path, project_root: Path, include_private: bool
) -> tuple[list[MissingDocstring], int, int]:
    """Analyze a single Python file for missing docstrings.

    Args:
        tree: AST tree of the file
        file_path: Path to the file
        project_root: Project root directory
        include_private: Include private methods/functions

    Returns:
        Tuple of (missing_docstrings, total_items, documented_items)
    """
    missing = []
    total = 0
    documented = 0

    relative_path = str(file_path.relative_to(project_root))

    for node in ast.walk(tree):
        # Analyze classes
        if isinstance(node, ast.ClassDef):
            if not include_private and node.name.startswith("_"):
                continue

            total += 1
            if ast.get_docstring(node):
                documented += 1
            else:
                missing.append(
                    MissingDocstring(
                        item_type="class",
                        name=node.name,
                        file_path=relative_path,
                        line_number=node.lineno,
                        signature=_get_class_signature(node),
                    )
                )

        # Analyze functions (including methods)
        elif isinstance(node, ast.FunctionDef):
            if not include_private and node.name.startswith("_"):
                continue

            total += 1
            if ast.get_docstring(node):
                documented += 1
            else:
                missing.append(
                    MissingDocstring(
                        item_type="function",
                        name=node.name,
                        file_path=relative_path,
                        line_number=node.lineno,
                        signature=_get_function_signature(node),
                    )
                )

    return missing, total, documented


def _get_class_signature(node: ast.ClassDef) -> str:
    """Get class signature.

    Args:
        node: ClassDef AST node

    Returns:
        Class signature string
    """
    bases = ", ".join(ast.unparse(base) for base in node.bases)
    if bases:
        return f"class {node.name}({bases})"
    return f"class {node.name}"


def _get_function_signature(node: ast.FunctionDef) -> str:
    """Get function signature.

    Args:
        node: FunctionDef AST node

    Returns:
        Function signature string
    """
    args_list = []

    # Add regular arguments
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args_list.append(arg_str)

    # Add *args if present
    if node.args.vararg:
        vararg_str = f"*{node.args.vararg.arg}"
        if node.args.vararg.annotation:
            vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
        args_list.append(vararg_str)

    # Add **kwargs if present
    if node.args.kwarg:
        kwarg_str = f"**{node.args.kwarg.arg}"
        if node.args.kwarg.annotation:
            kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
        args_list.append(kwarg_str)

    args_str = ", ".join(args_list)
    return_str = ""

    if node.returns:
        return_str = f" -> {ast.unparse(node.returns)}"

    return f"def {node.name}({args_str}){return_str}"


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
