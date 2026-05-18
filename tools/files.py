import glob
import os
from anthropic import beta_tool


@beta_tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 8000:
            return content[:8000] + f"\n... (truncated — file is {len(content)} chars)"
        return content
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Failed to read {path}: {e}"


@beta_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: Path to the file to write.
        content: Content to write to the file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Failed to write {path}: {e}"


@beta_tool
def list_files(directory: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching an optional glob pattern.

    Args:
        directory: Directory to list.
        pattern: Glob pattern to filter files (e.g. '*.py', '**/*.md').
    """
    try:
        matches = glob.glob(os.path.join(directory, pattern), recursive=True)
        matches.sort()
        if not matches:
            return f"No files matching '{pattern}' in {directory}"
        return "\n".join(matches[:200])
    except Exception as e:
        return f"Failed to list files: {e}"
