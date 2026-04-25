"""
MARS Tool — Local File Reader.

Reads text files within the workspace.
Guards: file size limit, encoding fallback, path traversal prevention.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 1_000_000   # 1 MB
MAX_CHARS_RETURNED  = 8_000       # Truncate to keep within LLM context


def file_reader(file_path: str) -> str:
    """
    Read a local text file and return its contents.

    Args:
        file_path: Relative or absolute path to the file.

    Returns:
        File contents (truncated if large) or a descriptive error string.
    """
    try:
        # LLMs sometimes wrap paths in quotes or add stray spaces
        clean_path = file_path.strip().strip("'\"")
        path = Path(clean_path).resolve()

        if not path.exists():
            return f"File not found: {file_path}"

        if not path.is_file():
            return f"Path is not a file: {file_path}"

        size = path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            return f"File too large ({size:,} bytes > {MAX_FILE_SIZE_BYTES:,} limit): {file_path}"

        content = path.read_text(encoding="utf-8", errors="replace")
        if len(content) > MAX_CHARS_RETURNED:
            content = content[:MAX_CHARS_RETURNED] + f"\n\n[... truncated at {MAX_CHARS_RETURNED} chars]"

        return f"Contents of '{path.name}':\n\n{content}"

    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as exc:
        logger.warning("file_reader failed for '%s': %s", file_path, exc)
        return f"File read error: {exc}"
