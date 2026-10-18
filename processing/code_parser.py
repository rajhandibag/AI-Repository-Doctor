
import ast
import hashlib


def parse_python_file(file_path, content):
    """
    Extract Python functions and classes while preserving
    source code, file paths, and line numbers.
    """

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [{
            "file_path": file_path,
            "item_type": "file",
            "item_name": file_path.split("/")[-1],
            "start_line": 1,
            "end_line": max(1, len(content.splitlines())),
            "content": content,
            "content_hash": hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest(),
        }]

    lines = content.splitlines()
    items = []

    # Include the whole file so imports and global variables
    # are not lost.
    items.append({
        "file_path": file_path,
        "item_type": "file",
        "item_name": file_path.split("/")[-1],
        "start_line": 1,
        "end_line": max(1, len(lines)),
        "content": content,
        "content_hash": hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
    })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            item_type = "function"
        elif isinstance(node, ast.ClassDef):
            item_type = "class"
        else:
            continue

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)

        source = "\n".join(lines[start_line - 1:end_line])

        items.append({
            "file_path": file_path,
            "item_type": item_type,
            "item_name": node.name,
            "start_line": start_line,
            "end_line": end_line,
            "content": source,
            "content_hash": hashlib.sha256(
                source.encode("utf-8")
            ).hexdigest(),
        })

    return items


def parse_repository(files):
    """Parse files returned by read_repository_zip()."""

    parsed_items = []

    for file in files:
        path = file["path"]
        content = file["content"]

        if path.lower().endswith(".py"):
            parsed_items.extend(parse_python_file(path, content))
        else:
            # Preserve documentation and configuration files.
            lines = content.splitlines()

            parsed_items.append({
                "file_path": path,
                "item_type": "file",
                "item_name": path.split("/")[-1],
                "start_line": 1,
                "end_line": max(1, len(lines)),
                "content": content,
                "content_hash": hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            })

    return parsed_items
