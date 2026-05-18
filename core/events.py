from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import json

# Optional hook set by the web server to broadcast events over WebSocket.
# Signature: (entry: dict) -> None — called synchronously after each log write.
_broadcast_hook: Optional[Callable[[dict], None]] = None


def set_broadcast_hook(fn: Callable[[dict], None]) -> None:
    global _broadcast_hook
    _broadcast_hook = fn


class EventLog:
    def __init__(self, events_dir: Path):
        self.dir = events_dir

    def _today_file(self) -> Path:
        return self.dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def log(
        self,
        event_type: str,
        data: Optional[dict] = None,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> None:
        entry = {
            "ts": datetime.now().isoformat(),
            "type": event_type,
            "task_id": task_id,
            "agent": agent,
            **(data or {}),
        }
        with open(self._today_file(), "a") as f:
            f.write(json.dumps(entry) + "\n")
        if _broadcast_hook:
            try:
                _broadcast_hook(entry)
            except Exception:
                pass

    def recent(self, n: int = 20) -> list:
        entries: list = []
        for path in sorted(self.dir.glob("*.jsonl"), reverse=True):
            try:
                lines = path.read_text().strip().splitlines()
                for line in reversed(lines):
                    if line.strip():
                        entries.append(json.loads(line))
                        if len(entries) >= n:
                            return entries
            except Exception:
                pass
        return entries

    def format_entry(self, entry: dict) -> str:
        ts = entry.get("ts", "")[:19].replace("T", " ")
        etype = entry.get("type", "")
        task_id = entry.get("task_id") or ""
        agent = entry.get("agent") or ""
        title = entry.get("title", "")
        parts = [ts, f"{etype:<20}", task_id, agent]
        if title:
            parts.append(title[:50])
        return "  ".join(p for p in parts if p)
