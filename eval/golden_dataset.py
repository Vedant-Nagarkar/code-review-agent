GOLDEN_DATASET = {
    "security": [
        {"name": "sql_injection", "expected_flag": True, "code": '''
import sqlite3
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()
'''},
        {"name": "hardcoded_secret", "expected_flag": True, "code": '''
def connect_to_api():
    api_key = "sk-proj-abc123def456ghi789"
    return call_api(api_key)
'''},
        {"name": "command_injection", "expected_flag": True, "code": '''
import os
def run_backup(filename):
    os.system("tar -cvf backup.tar " + filename)
'''},
        {"name": "parameterized_query", "expected_flag": False, "code": '''
import sqlite3
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()
'''},
        {"name": "env_var_secret", "expected_flag": False, "code": '''
import os
def connect_to_api():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    return call_api(api_key)
'''},
    ],
    "performance": [
        {"name": "nested_loop_duplicates", "expected_flag": True, "code": '''
def find_duplicates(list1, list2):
    duplicates = []
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                duplicates.append(item1)
    return duplicates
'''},
        {"name": "repeated_file_read", "expected_flag": True, "code": '''
def process_records(record_ids):
    results = []
    for record_id in record_ids:
        with open("data.json") as f:
            data = json.load(f)
        results.append(data.get(record_id))
    return results
'''},
        {"name": "list_membership_in_loop", "expected_flag": True, "code": '''
def filter_valid(items, valid_ids):
    result = []
    for item in items:
        if item.id in valid_ids:
            result.append(item)
    return result
'''},
        {"name": "simple_linear_scan", "expected_flag": False, "code": '''
def find_first_match(items, target):
    for item in items:
        if item == target:
            return item
    return None
'''},
        {"name": "set_based_membership", "expected_flag": False, "code": '''
def filter_valid(items, valid_ids):
    valid_set = set(valid_ids)
    return [item for item in items if item.id in valid_set]
'''},
    ],
    "style": [
        {"name": "no_docstring_bad_names", "expected_flag": True, "code": '''
def f(a, b, c):
    x = a * 47
    y = b + x
    return y - c
'''},
        {"name": "deeply_nested_no_docs", "expected_flag": True, "code": '''
def process(d):
    if d:
        if d.get("x"):
            if d["x"] > 0:
                return d["x"] * 2
    return None
'''},
        {"name": "inconsistent_naming", "expected_flag": True, "code": '''
def calculate_Total(itemList, TaxRate):
    total_amount = 0
    for I in itemList:
        total_amount += I
    return total_amount * (1 + TaxRate)
'''},
        {"name": "clean_documented_function", "expected_flag": False, "code": '''
def calculate_total(items: list[float], tax_rate: float) -> float:
    """Calculate the total price of items including tax."""
    subtotal = sum(items)
    return subtotal * (1 + tax_rate)
'''},
        {"name": "clean_documented_class", "expected_flag": False, "code": '''
class ShoppingCart:
    """A simple shopping cart that tracks items and computes totals."""

    def __init__(self):
        self.items: list[float] = []

    def add_item(self, price: float) -> None:
        """Add an item's price to the cart."""
        self.items.append(price)

    def total(self) -> float:
        """Return the sum of all item prices in the cart."""
        return sum(self.items)
'''},
    ],
    "test_coverage": [
        {"name": "branching_no_tests", "expected_flag": True, "code": '''
def divide(a, b):
    if b == 0:
        return None
    if a < 0 or b < 0:
        return -(abs(a) / abs(b))
    return a / b
'''},
        {"name": "input_parsing_no_tests", "expected_flag": True, "code": '''
def parse_age(value):
    age = int(value)
    if age < 0 or age > 150:
        raise ValueError("Invalid age")
    return age
'''},
        {"name": "class_multiple_methods_no_tests", "expected_flag": True, "code": '''
class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        return a / b
'''},
        {"name": "function_with_test_suite", "expected_flag": False, "code": '''
def divide(a, b):
    if b == 0:
        return None
    return a / b

def test_divide_normal():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    assert divide(10, 0) is None

def test_divide_negative():
    assert divide(-10, 2) == -5
'''},
        {"name": "simple_function_with_test", "expected_flag": False, "code": '''
def is_even(n):
    return n % 2 == 0

def test_is_even():
    assert is_even(4) is True
    assert is_even(3) is False
    assert is_even(0) is True
'''},
    ],
}