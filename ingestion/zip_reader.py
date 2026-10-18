
import io
import stat
import zipfile
from pathlib import PurePosixPath

MAX_FILES = 500
MAX_FILE_SIZE = 1 * 1024 * 1024       # 1 MB per file
MAX_TOTAL_SIZE = 50 * 1024 * 1024    # 50 MB uncompressed

ALLOWED_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml"
}

ALLOWED_FILENAMES = {
    "requirements.txt",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}


def is_supported_file(path):
    return (
        path.suffix.lower() in ALLOWED_EXTENSIONS
        or path.name.lower() in ALLOWED_FILENAMES
    )


def read_repository_zip(zip_bytes):
    """Read supported text files from a ZIP without extracting to disk."""

    if len(zip_bytes) > 20 * 1024 * 1024:
        raise ValueError("ZIP upload exceeds the 20 MB limit.")

    files = []
    total_size = 0

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError("The uploaded file is not a valid ZIP.") from exc

    with archive:
        entries = archive.infolist()

        if len(entries) > 5000:
            raise ValueError("ZIP contains too many entries.")

        for entry in entries:
            raw_name = entry.filename

            # Reject absolute paths and Windows-style path tricks.
            if raw_name.startswith(("/", "\\")) or "\\" in raw_name:
                raise ValueError(f"Unsafe ZIP path: {raw_name}")

            path = PurePosixPath(raw_name)

            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe ZIP path: {raw_name}")

            if entry.is_dir():
                continue

            # Ignore symbolic links.
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                continue

            if any(part in IGNORED_DIRECTORIES for part in path.parts):
                continue

            if not is_supported_file(path):
                continue

            if len(files) >= MAX_FILES:
                raise ValueError("Repository exceeds the 500-file limit.")

            if entry.file_size > MAX_FILE_SIZE:
                raise ValueError(f"File exceeds 1 MB: {raw_name}")

            total_size += entry.file_size

            if total_size > MAX_TOTAL_SIZE:
                raise ValueError("Total uncompressed file size exceeds 50 MB.")

            try:
                content_bytes = archive.read(entry)
                content = content_bytes.decode("utf-8")
            except (UnicodeDecodeError, OSError, zipfile.BadZipFile):
                # Skip binary files or files that cannot be read safely.
                continue

            files.append({
                "path": path.as_posix(),
                "content": content,
                "size": len(content_bytes),
            })

    return files
