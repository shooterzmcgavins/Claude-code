from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import uuid

from core.markdown import parse_frontmatter, build_frontmatter, extract_section


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    NEEDS_APPROVAL = "needs_approval"
    COMPLETE = "complete"
    FAILED = "failed"


STATUS_SYMBOLS = {
    TaskStatus.PENDING: "○",
    TaskStatus.IN_PROGRESS: "◉",
    TaskStatus.NEEDS_APPROVAL: "⚠",
    TaskStatus.COMPLETE: "✓",
    TaskStatus.FAILED: "✗",
}


@dataclass
class Task:
    id: str
    title: str
    description: str
    agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    updated_at: str = ""
    result: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(cls, title: str, description: str = "") -> Task:
        now = datetime.now().isoformat()
        return cls(
            id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            title=title,
            description=description or title,
            created_at=now,
            updated_at=now,
        )

    def status_line(self) -> str:
        sym = STATUS_SYMBOLS.get(self.status, "?")
        agent_col = f"  [{self.agent}]" if self.agent else ""
        ts = self.created_at[:16].replace("T", " ") if self.created_at else ""
        return f"{sym} {self.id}  {self.status.value:<14}{agent_col:<14}  {ts}  {self.title[:60]}"


class TaskStore:
    """Persists tasks as Obsidian-friendly markdown files with YAML frontmatter.

    File layout:
        workspace/tasks/TASK-XXXXXX.md

    Each file has machine-readable frontmatter (id, status, agent, timestamps)
    and a human-readable body with Description and optional Result sections.
    """

    def __init__(self, tasks_dir: Path):
        self.dir = tasks_dir

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(self, task: Task) -> None:
        task.updated_at = datetime.now().isoformat()
        path = self.dir / f"{task.id}.md"

        meta = {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "agent": task.agent or "",
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "tags": task.tags,
        }

        body = self._render_body(task)
        path.write_text(build_frontmatter(meta) + "\n" + body, encoding="utf-8")

    @staticmethod
    def _render_body(task: Task) -> str:
        lines = [
            f"# {task.id} — {task.title}",
            "",
            "## Description",
            "",
            task.description,
            "",
        ]
        if task.result:
            lines += ["## Result", "", task.result, ""]
        return "\n".join(lines)

    # ── Read ──────────────────────────────────────────────────────────────────

    def load(self, task_id: str) -> Optional[Task]:
        path = self.dir / f"{task_id}.md"
        if not path.exists():
            return None
        return self._parse(path)

    def list_all(self) -> List[Task]:
        tasks = []
        for path in sorted(self.dir.glob("TASK-*.md"), reverse=True):
            try:
                t = self._parse(path)
                if t:
                    tasks.append(t)
            except Exception:
                pass
        return tasks

    def list_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self.list_all() if t.status == status]

    def _parse(self, path: Path) -> Optional[Task]:
        content = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        if not meta:
            return None

        description = extract_section(body, "Description") or meta.get("title", "")
        result = extract_section(body, "Result") or None

        tags = meta.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        return Task(
            id=meta.get("id", path.stem),
            title=meta.get("title", ""),
            description=description,
            agent=meta.get("agent") or None,
            status=TaskStatus(meta.get("status", "pending")),
            created_at=meta.get("created_at", ""),
            updated_at=meta.get("updated_at", ""),
            result=result,
            tags=tags,
        )
