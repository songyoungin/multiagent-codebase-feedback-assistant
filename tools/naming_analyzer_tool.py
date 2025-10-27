"""Naming quality analyzer tool."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from common.logger import get_logger
from common.schemas import DEFAULT_EXCLUDE_PATTERNS, NamingAnalysisResult, NamingItem

logger = get_logger(__name__)


def analyze_naming_quality(
    project_path: str,
    exclude_patterns: Optional[list[str]] = None,  # noqa: UP045 (incompatible with google-adk function parsing)
    max_items: int = 30,
    include_private: bool = False,
) -> dict[str, Any]:
    """Extract naming information for quality analysis.

    Args:
        project_path: Root path to analyze
        exclude_patterns: List of patterns to exclude from analysis (optional)
        max_items: Maximum number of items to analyze (to manage LLM context)
        include_private: Include private items (starting with _)

    Returns:
        Dictionary representation of NamingAnalysisResult object
    """
    logger.info(f"Starting naming quality analysis at: {project_path}")

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

    # Extract naming items
    naming_items: list[NamingItem] = []
    files_analyzed = 0

    for py_file in root.rglob("*.py"):
        # Check exclusion patterns
        relative_path = str(py_file.relative_to(root))
        if any(pattern in relative_path for pattern in exclude_patterns):
            continue

        try:
            with open(py_file, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))

            # Extract naming items from this file
            file_items = _extract_naming_items(tree, relative_path, root, include_private)
            naming_items.extend(file_items)
            files_analyzed += 1

            # Stop if we've collected enough items
            if len(naming_items) >= max_items:
                logger.info(f"Reached max_items limit ({max_items}), stopping analysis")
                naming_items = naming_items[:max_items]
                break

        except Exception as e:
            logger.warning(f"Failed to parse {py_file}: {e}")
            continue

    logger.info(f"Analysis complete: {files_analyzed} files, {len(naming_items)} items")

    # Create result
    result = NamingAnalysisResult(
        project_path=str(root),
        files_analyzed=files_analyzed,
        total_items=len(naming_items),
        naming_items=naming_items,
        analyzed_at=datetime.now(),
    )

    return result.model_dump()


def _extract_naming_items(
    tree: ast.AST, file_path: str, project_root: Path, include_private: bool
) -> list[NamingItem]:
    """Extract naming items (variables, functions, classes, parameters) from AST.

    Args:
        tree: AST tree to analyze
        file_path: Relative file path
        project_root: Project root path
        include_private: Include private items

    Returns:
        List of NamingItem objects
    """
    items: list[NamingItem] = []

    for node in ast.walk(tree):
        # Extract class names
        if isinstance(node, ast.ClassDef):
            if not include_private and node.name.startswith("_"):
                continue

            items.append(
                NamingItem(
                    item_type="class",
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    context_code=_get_class_signature(node),
                    type_hint=None,
                    docstring=ast.get_docstring(node),
                    scope="class",
                )
            )

        # Extract function/method names
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if not include_private and node.name.startswith("_") and node.name != "__init__":
                continue

            items.append(
                NamingItem(
                    item_type="function",
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    context_code=_get_function_signature(node),
                    type_hint=_get_return_type(node),
                    docstring=ast.get_docstring(node),
                    scope=_get_function_scope(node),
                )
            )

            # Extract parameter names
            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                if not include_private and arg.arg.startswith("_"):
                    continue

                items.append(
                    NamingItem(
                        item_type="parameter",
                        name=arg.arg,
                        file_path=file_path,
                        line_number=arg.lineno if hasattr(arg, "lineno") else node.lineno,
                        context_code=f"Parameter in {node.name}()",
                        type_hint=_get_arg_type(arg),
                        docstring=None,
                        scope="parameter",
                    )
                )

        # Extract variable assignments
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if not include_private and var_name.startswith("_"):
                        continue

                    # Skip constants (ALL_CAPS)
                    if var_name.isupper():
                        continue

                    items.append(
                        NamingItem(
                            item_type="variable",
                            name=var_name,
                            file_path=file_path,
                            line_number=node.lineno,
                            context_code=ast.unparse(node),
                            type_hint=_get_assigned_type(node),
                            docstring=None,
                            scope="local",
                        )
                    )

    return items


def _get_class_signature(node: ast.ClassDef) -> str:
    """Get class signature."""
    bases = ", ".join(ast.unparse(base) for base in node.bases) if node.bases else ""
    if bases:
        return f"class {node.name}({bases})"
    return f"class {node.name}"


def _get_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Get function signature with parameters and return type."""
    args_str = _format_arguments(node.args)
    return_annotation = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({args_str}){return_annotation}"


def _format_arguments(args: ast.arguments) -> str:
    """Format function arguments."""
    formatted_args = []

    # Regular arguments
    for arg in args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        formatted_args.append(arg_str)

    # *args
    if args.vararg:
        arg_str = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            arg_str += f": {ast.unparse(args.vararg.annotation)}"
        formatted_args.append(arg_str)

    # **kwargs
    if args.kwarg:
        arg_str = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            arg_str += f": {ast.unparse(args.kwarg.annotation)}"
        formatted_args.append(arg_str)

    return ", ".join(formatted_args)


def _get_return_type(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Get return type annotation."""
    if node.returns:
        return ast.unparse(node.returns)
    return None


def _get_arg_type(arg: ast.arg) -> str | None:
    """Get argument type annotation."""
    if arg.annotation:
        return ast.unparse(arg.annotation)
    return None


def _get_assigned_type(node: ast.Assign) -> str | None:
    """Get type of assigned value."""
    if isinstance(node.value, ast.Constant):
        return type(node.value.value).__name__
    elif isinstance(node.value, ast.List):
        return "list"
    elif isinstance(node.value, ast.Dict):
        return "dict"
    elif isinstance(node.value, ast.Set):
        return "set"
    elif isinstance(node.value, ast.Tuple):
        return "tuple"
    elif isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name):
            return node.value.func.id
    return None


def _get_function_scope(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Determine if function is a method or standalone function."""
    # Check if first parameter is 'self' or 'cls'
    if node.args.args:
        first_arg = node.args.args[0].arg
        if first_arg in ("self", "cls"):
            return "method"
    return "function"
