"""Persist and retrieve chat sessions from workspace/chats/*.jsonl."""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def _chats_dir(workspace_chats: Path) -> Path:
    workspace_chats.mkdir(parents=True, exist_ok=True)
    return workspace_chats


def new_session_id() -> str:
    date = datetime.now().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"{date}-{short}"


def append(chats_dir: Path, session_id: str, role: str, content: str,
           agent: Optional[str] = None, task_id: Optional[str] = None) -> None:
    entry = {
        "ts": datetime.now().isoformat(),
        "session_id": session_id,
        "role": role,
        "content": content,
        "agent": agent,
        "task_id": task_id,
    }
    path = _chats_dir(chats_dir) / f"{session_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load(chats_dir: Path, session_id: str) -> list[dict]:
    path = chats_dir / f"{session_id}.jsonl"
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def list_sessions(chats_dir: Path) -> list[dict]:
    sessions = []
    for path in sorted(chats_dir.glob("*.jsonl"), reverse=True):
        try:
            lines = [l for l in path.read_text().splitlines() if l.strip()]
            if not lines:
                continue
            first = json.loads(lines[0])
            last = json.loads(lines[-1])
            sessions.append({
                "session_id": path.stem,
                "created_at": first.get("ts", ""),
                "updated_at": last.get("ts", ""),
                "message_count": len(lines),
                "preview": first.get("content", "")[:80],
            })
        except Exception:
            pass
    return sessions
