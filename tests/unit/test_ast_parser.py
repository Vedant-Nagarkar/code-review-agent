from tools.ast_parser import run_ast_parser


def test_detects_missing_docstring():
    code = """
def add(a, b):
    return a + b
"""
    result = run_ast_parser(code, "python")
    assert "Missing docstrings" in result
    assert "add" in result


def test_detects_present_docstring():
    code = '''
def add(a, b):
    """Adds two numbers."""
    return a + b
'''
    result = run_ast_parser(code, "python")
    assert "Missing docstrings" not in result


def test_counts_functions_and_classes():
    code = """
def foo():
    pass

def bar():
    pass

class Baz:
    pass
"""
    result = run_ast_parser(code, "python")
    assert "Total functions: 2" in result
    assert "Total classes: 1" in result


def test_detects_magic_numbers():
    code = """
def calculate(x):
    return x * 47
"""
    result = run_ast_parser(code, "python")
    assert "Magic numbers detected" in result
    assert "47" in result


def test_ignores_common_non_magic_numbers():
    code = """
def check(x):
    if x == 0 or x == 1 or x == -1:
        return True
    return False
"""
    result = run_ast_parser(code, "python")
    assert "Magic numbers detected" not in result


def test_detects_nested_functions():
    code = """
def outer():
    def inner():
        pass
    return inner
"""
    result = run_ast_parser(code, "python")
    assert "Nested functions" in result
    assert "inner" in result


def test_non_python_language_skips_analysis():
    result = run_ast_parser("function foo() {}", "javascript")
    assert "skipped" in result.lower()


def test_syntax_error_reported_clearly():
    broken_code = "def foo(:\n    pass"
    result = run_ast_parser(broken_code, "python")
    assert "syntax error" in result.lower()


def test_empty_code_no_functions_or_classes():
    result = run_ast_parser("x = 1\ny = 2", "python")
    assert "No functions or classes detected" in result