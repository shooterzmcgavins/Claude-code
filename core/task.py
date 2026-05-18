from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import json
import uuid


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

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Task:
        d = dict(d)
        d["status"] = TaskStatus(d.get("status", "pending"))
        d.setdefault("tags", [])
        d.setdefault("result", None)
        d.setdefault("agent", None)
        d.setdefault("updated_at", d.get("created_at", ""))
        return cls(**d)

    def status_line(self) -> str:
        sym = STATUS_SYMBOLS.get(self.status, "?")
        agent = f"  [{self.agent}]" if self.agent else ""
        ts = self.created_at[:16].replace("T", " ") if self.created_at else ""
        return f"{sym} {self.id}  {self.status.value:<12}{agent:<12}  {ts}  {self.title[:60]}"


class TaskStore:
    def __init__(self, tasks_dir: Path):
        self.dir = tasks_dir

    def save(self, task: Task) -> None:
        task.updated_at = datetime.now().isoformat()
        (self.dir / f"{task.id}.json").write_text(json.dumps(task.to_dict(), indent=2))

    def load(self, task_id: str) -> Optional[Task]:
        path = self.dir / f"{task_id}.json"
        if not path.exists():
            return None
        return Task.from_dict(json.loads(path.read_text()))

    def list_all(self) -> List[Task]:
        tasks = []
        for path in sorted(self.dir.glob("TASK-*.json"), reverse=True):
            try:
                tasks.append(Task.from_dict(json.loads(path.read_text())))
            except Exception:
                pass
        return tasks

    def list_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self.list_all() if t.status == status]
