import ast
import json


def run_ast_parser(code: str, language: str) -> str:
    # AST parsing only works on Python code
    if language.lower() != "python":
        return "AST analysis skipped — only supported for Python code."

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"AST parsing failed — syntax error in code: {str(e)}"

    metrics = {
        "total_functions": 0,
        "total_classes": 0,
        "functions": [],
        "classes": [],
        "missing_docstrings": [],
        "magic_numbers": [],
        "nested_functions": [],
    }

    for node in ast.walk(tree):
        # Count and analyze functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            metrics["total_functions"] += 1

            func_info = {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "length": node.end_lineno - node.lineno + 1,
                "args": [arg.arg for arg in node.args.args],
                "has_docstring": (
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                ) if node.body else False
            }

            metrics["functions"].append(func_info)

            if not func_info["has_docstring"]:
                metrics["missing_docstrings"].append(f"function '{node.name}' at line {node.lineno}")

        # Count and analyze classes
        if isinstance(node, ast.ClassDef):
            metrics["total_classes"] += 1
            class_info = {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "length": node.end_lineno - node.lineno + 1,
                "has_docstring": (
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                ) if node.body else False
            }
            metrics["classes"].append(class_info)

            if not class_info["has_docstring"]:
                metrics["missing_docstrings"].append(f"class '{node.name}' at line {node.lineno}")

        # Detect magic numbers
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if node.value not in (0, 1, -1, 2, 100):
                metrics["magic_numbers"].append(
                    f"value {node.value} at line {node.lineno}"
                )

    # Detect nested functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is not node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics["nested_functions"].append(
                        f"'{child.name}' nested inside '{node.name}' at line {child.lineno}"
                    )

    # Build readable summary for the LLM
    summary_lines = [
        f"Total functions: {metrics['total_functions']}",
        f"Total classes: {metrics['total_classes']}",
    ]

    if metrics["functions"]:
        summary_lines.append("\nFunction details:")
        for f in metrics["functions"]:
            summary_lines.append(
                f"  - {f['name']}(): lines {f['line_start']}-{f['line_end']} "
                f"({f['length']} lines, {len(f['args'])} args, "
                f"docstring: {f['has_docstring']})"
            )

    if metrics["missing_docstrings"]:
        summary_lines.append(f"\nMissing docstrings: {', '.join(metrics['missing_docstrings'])}")

    if metrics["magic_numbers"]:
        summary_lines.append(f"\nMagic numbers detected: {', '.join(metrics['magic_numbers'][:10])}")

    if metrics["nested_functions"]:
        summary_lines.append(f"\nNested functions: {', '.join(metrics['nested_functions'])}")

    if metrics["total_functions"] == 0 and metrics["total_classes"] == 0:
        summary_lines.append("\nNo functions or classes detected — code may be purely procedural.")

    return "\n".join(summary_lines)