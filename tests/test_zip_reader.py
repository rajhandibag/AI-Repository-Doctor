
import io
import zipfile

import pytest

from ingestion.zip_reader import read_repository_zip


def make_zip(entries):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)

    return buffer.getvalue()


def test_reads_python_file():
    data = make_zip([
        ("main.py", "print('Hello')"),
        ("README.md", "# My project"),
    ])

    result = read_repository_zip(data)

    assert len(result) == 2
    assert result[0]["path"] == "main.py"
    assert result[0]["content"] == "print('Hello')"


def test_ignores_unsupported_files():
    data = make_zip([
        ("main.py", "x = 10"),
        ("photo.png", "not a real image"),
    ])

    result = read_repository_zip(data)

    assert len(result) == 1
    assert result[0]["path"] == "main.py"


def test_ignores_dependency_directories():
    data = make_zip([
        ("main.py", "print('hello')"),
        ("node_modules/package/index.py", "ignored"),
    ])

    result = read_repository_zip(data)

    assert len(result) == 1


def test_rejects_path_traversal():
    data = make_zip([
        ("../outside.py", "unsafe"),
    ])

    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        read_repository_zip(data)


def test_rejects_invalid_zip():
    with pytest.raises(ValueError, match="valid ZIP"):
        read_repository_zip(b"this is not a zip file")

def test_rejects_file_larger_than_limit():
    large_content = "A" * (1024 * 1024 + 1)

    data = make_zip([
        ("large.py", large_content),
    ])

    with pytest.raises(ValueError, match="exceeds 1 MB"):
        read_repository_zip(data)