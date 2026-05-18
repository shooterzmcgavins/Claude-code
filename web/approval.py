"""Thread-safe approval system for shell commands.

When a SpecialistAgent wants to run a shell command it calls
request_approval(), which blocks the agent thread via threading.Event
until the web UI resolves it (approve/reject) or the timeout expires.
"""
from __future__ import annotations
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from web import broadcaster


@dataclass
class ApprovalRequest:
    id: str
    agent: str
    command: str
    task_id: Optional[str]
    created_at: str
    _event: threading.Event = field(default_factory=threading.Event, repr=False)
    _result: bool = field(default=False, repr=False)


class ApprovalManager:
    TIMEOUT = 300  # seconds

    def __init__(self) -> None:
        self._pending: dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()

    def request_approval(self, agent: str, command: str, task_id: Optional[str] = None) -> bool:
        req = ApprovalRequest(
            id=f"APR-{uuid.uuid4().hex[:6].upper()}",
            agent=agent,
            command=command,
            task_id=task_id,
            created_at=datetime.now().isoformat(),
        )
        with self._lock:
            self._pending[req.id] = req

        broadcaster.emit({
            "type": "approval.pending",
            "ts": req.created_at,
            "approval_id": req.id,
            "agent": agent,
            "command": command,
            "task_id": task_id,
        })

        req._event.wait(timeout=self.TIMEOUT)

        with self._lock:
            self._pending.pop(req.id, None)

        return req._result

    def resolve(self, approval_id: str, approved: bool) -> bool:
        with self._lock:
            req = self._pending.get(approval_id)
        if req is None:
            return False

        req._result = approved
        req._event.set()

        broadcaster.emit({
            "type": "approval.resolved",
            "ts": datetime.now().isoformat(),
            "approval_id": approval_id,
            "approved": approved,
        })
        return True

    def pending(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": r.id,
                    "agent": r.agent,
                    "command": r.command,
                    "task_id": r.task_id,
                    "created_at": r.created_at,
                }
                for r in self._pending.values()
            ]
