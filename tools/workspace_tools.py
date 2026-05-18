"""Workspace-aware tools that read/write within the workspace directory."""
from typing import Optional
from pathlib import Path
from datetime import datetime

_workspace_root: Optional[Path] = None


def init_workspace_tools(workspace) -> None:
    global _workspace_root
    _workspace_root = workspace.root


def _ws() -> Path:
    if _workspace_root is None:
        raise RuntimeError("Workspace not initialized — call init_workspace_tools first")
    return _workspace_root


def write_report(task_id: str, content: str) -> str:
    """Write a task report to the workspace reports directory.

    Args:
        task_id: The task ID this report belongs to (e.g. TASK-A1B2C3).
        content: The markdown content of the report.
    """
    reports_dir = _ws() / "reports"
    reports_dir.mkdir(exist_ok=True)
    path = reports_dir / f"{task_id}.md"
    header = f"# Report: {task_id}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    path.write_text(header + content)
    return f"Report saved to workspace/reports/{task_id}.md"


def read_memory(key: str) -> str:
    """Read a memory entry from the workspace memory store.

    Args:
        key: Memory key to read (e.g. 'project-context', 'team-conventions').
             Use 'index' to list all available memory keys.
    """
    memory_dir = _ws() / "memory"
    if key == "index":
        files = list(memory_dir.glob("*.md"))
        if not files:
            return "No memory entries yet."
        return "Available memory keys:\n" + "\n".join(f"  - {f.stem}" for f in sorted(files))
    path = memory_dir / f"{key}.md"
    if not path.exists():
        return f"No memory entry for key '{key}'. Use read_memory('index') to see available keys."
    return path.read_text()


def write_memory(key: str, content: str) -> str:
    """Persist information to the workspace memory store for future reference.

    Args:
        key: Memory key (e.g. 'project-context', 'api-endpoints', 'team-conventions').
             Use lowercase with hyphens. Overwrites any existing entry for this key.
        content: Markdown content to store.
    """
    memory_dir = _ws() / "memory"
    memory_dir.mkdir(exist_ok=True)
    path = memory_dir / f"{key}.md"
    header = f"# Memory: {key}\n\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    path.write_text(header + content)
    return f"Memory saved: workspace/memory/{key}.md"
