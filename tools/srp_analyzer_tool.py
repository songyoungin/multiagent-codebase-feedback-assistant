"""SRP (Single Responsibility Principle) analyzer tool."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from common.logger import get_logger
from common.schemas import DEFAULT_EXCLUDE_PATTERNS, CodeItem, SRPAnalysisResult

logger = get_logger(__name__)


def analyze_srp_violations(
    project_path: str,
    exclude_patterns: Optional[list[str]] = None,  # noqa: UP045 (incompatible with google-adk function parsing)
    max_items: int = 20,
    include_private: bool = False,
) -> dict[str, Any]:
    """Extract code items for SRP violation analysis.

    Args:
        project_path: Root path to analyze
        exclude_patterns: List of patterns to exclude from analysis (optional)
        max_items: Maximum number of items to analyze (to manage LLM context)
        include_private: Include private methods/functions (starting with _)

    Returns:
        Dictionary representation of SRPAnalysisResult object
    """
    logger.info(f"Starting SRP analysis at: {project_path}")

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

    # Extract code items
    code_items: list[CodeItem] = []
    files_analyzed = 0

    for py_file in root.rglob("*.py"):
        # Check exclude patterns
        if _should_exclude(py_file, root, exclude_patterns):
            continue

        # Stop if we've collected enough items
        if len(code_items) >= max_items:
            logger.info(f"Reached max_items limit ({max_items}), stopping collection")
            break

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            file_items = _extract_code_items(tree, py_file, root, include_private)
            code_items.extend(file_items)
            files_analyzed += 1

            # Trim if exceeded max_items
            if len(code_items) > max_items:
                code_items = code_items[:max_items]
                break

        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Error processing {py_file}: {e}")

    logger.info(f"Analysis complete: {files_analyzed} files analyzed, {len(code_items)} code items extracted")

    # Create result and return as dictionary
    result = SRPAnalysisResult(
        project_path=project_path,
        files_analyzed=files_analyzed,
        total_items=len(code_items),
        code_items=code_items,
        analyzed_at=datetime.now(),
    ).model_dump()

    return result


def _extract_code_items(tree: ast.AST, file_path: Path, project_root: Path, include_private: bool) -> list[CodeItem]:
    """Extract code items (functions and classes) from a file.

    Args:
        tree: AST tree of the file
        file_path: Path to the file
        project_root: Project root directory
        include_private: Include private methods/functions

    Returns:
        List of CodeItem objects
    """
    items = []
    relative_path = str(file_path.relative_to(project_root))

    # Read file content for extracting full code
    file_content = file_path.read_text(encoding="utf-8")
    lines = file_content.split("\n")

    for node in ast.walk(tree):
        # Extract classes
        if isinstance(node, ast.ClassDef):
            if not include_private and node.name.startswith("_"):
                continue

            # Get full class code
            full_code = _extract_node_code(node, lines)

            # Get method names
            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]

            # Get imports used in class
            imports = _extract_imports_from_node(node)

            items.append(
                CodeItem(
                    item_type="class",
                    name=node.name,
                    file_path=relative_path,
                    line_number=node.lineno,
                    signature=_get_class_signature(node),
                    full_code=full_code,
                    parameters_count=0,  # Classes don't have parameters
                    length_lines=node.end_lineno - node.lineno + 1 if node.end_lineno else 0,
                    calls_functions=methods,  # For classes, list methods
                    uses_imports=imports,
                    docstring=ast.get_docstring(node),
                )
            )

        # Extract functions (including methods)
        elif isinstance(node, ast.FunctionDef):
            if not include_private and node.name.startswith("_"):
                continue

            # Get full function code
            full_code = _extract_node_code(node, lines)

            # Get function calls
            calls = _extract_function_calls(node)

            # Get imports used
            imports = _extract_imports_from_node(node)

            # Count parameters
            param_count = len(node.args.args) + (1 if node.args.vararg else 0) + (1 if node.args.kwarg else 0)

            items.append(
                CodeItem(
                    item_type="function",
                    name=node.name,
                    file_path=relative_path,
                    line_number=node.lineno,
                    signature=_get_function_signature(node),
                    full_code=full_code,
                    parameters_count=param_count,
                    length_lines=node.end_lineno - node.lineno + 1 if node.end_lineno else 0,
                    calls_functions=calls,
                    uses_imports=imports,
                    docstring=ast.get_docstring(node),
                )
            )

    return items


def _extract_node_code(node: ast.AST, lines: list[str]) -> str:
    """Extract full code of a node.

    Args:
        node: AST node
        lines: Lines of the file

    Returns:
        Full code as string
    """
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return ""

    start = node.lineno - 1  # Convert to 0-indexed
    end = node.end_lineno if node.end_lineno else start + 1

    return "\n".join(lines[start:end])


def _extract_function_calls(node: ast.FunctionDef) -> list[str]:
    """Extract function calls from a function.

    Args:
        node: FunctionDef AST node

    Returns:
        List of function names called
    """
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return list(set(calls))  # Remove duplicates


def _extract_imports_from_node(node: ast.AST) -> list[str]:
    """Extract imports used in a node.

    Args:
        node: AST node

    Returns:
        List of imported module names
    """
    imports = []
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            for alias in child.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(child, ast.ImportFrom):
            if child.module:
                imports.append(child.module.split(".")[0])
    return list(set(imports))  # Remove duplicates


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
