GOLDEN_DATASET = [
    {
        "name": "sql_injection",
        "code": '''
import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()
''',
        "expect": {
            "security_has_findings": True,
            "min_security_severity": "medium",
        }
    },
    {
        "name": "clean_simple_function",
        "code": '''
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
''',
        "expect": {
            "security_has_findings": False,
        }
    },
    {
        "name": "missing_docstring",
        "code": '''
def process(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''',
        "expect": {
            "style_has_findings": True,
        }
    },
    {
        "name": "nested_loop_performance",
        "code": '''
def find_duplicates(list1, list2):
    duplicates = []
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                duplicates.append(item1)
    return duplicates
''',
        "expect": {
            "performance_has_findings": True,
        }
    },
    {
        "name": "hardcoded_secret",
        "code": '''
def connect_to_api():
    api_key = "sk-proj-abc123def456ghi789"
    return call_api(api_key)
''',
        "expect": {
            "security_has_findings": True,
            "min_security_severity": "medium",
        }
    },
]