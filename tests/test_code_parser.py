
from processing.code_parser import parse_python_file, parse_repository


def test_extracts_function_and_line_numbers():
    code = (
        "import math\n"
        "\n"
        "def calculate(value):\n"
        "    return math.sqrt(value)\n"
    )

    items = parse_python_file("utils.py", code)

    function = next(
        item for item in items
        if item["item_type"] == "function"
    )

    assert function["item_name"] == "calculate"
    assert function["file_path"] == "utils.py"
    assert function["start_line"] == 3
    assert function["end_line"] == 4


def test_extracts_class():
    code = (
        "class LoanModel:\n"
        "    def predict(self, data):\n"
        "        return data\n"
    )

    items = parse_python_file("model.py", code)

    assert any(
        item["item_type"] == "class"
        and item["item_name"] == "LoanModel"
        for item in items
    )


def test_handles_invalid_python():
    code = "def broken(:\n    pass"

    items = parse_python_file("broken.py", code)

    assert len(items) == 1
    assert items[0]["item_type"] == "file"
    assert items[0]["content"] == code


def test_preserves_documentation_files():
    files = [{
        "path": "README.md",
        "content": "# Project\nThis predicts loan approval.",
        "size": 36,
    }]

    items = parse_repository(files)

    assert len(items) == 1
    assert items[0]["file_path"] == "README.md"
    assert items[0]["item_type"] == "file"
