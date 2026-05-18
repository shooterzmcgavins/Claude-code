import json
from typing import Optional

from config import Config, HAIKU
from core.workspace import Workspace
from core.task import Task, TaskStore
from core.events import EventLog
from .base import BaseAgent
from .roles import SUPERVISOR_SYSTEM_PROMPT, ROLES


class Supervisor(BaseAgent):
    name = "supervisor"

    @property
    def system_prompt(self) -> str:
        return SUPERVISOR_SYSTEM_PROMPT

    def route(self, task_description: str) -> str:
        """Determine which agent should handle this task. Returns the agent name."""
        task_lower = task_description.lower()

        # Keyword matching first — zero API cost
        best_role = None
        best_count = 0
        for role, cfg in ROLES.items():
            count = sum(1 for kw in cfg["keywords"] if kw in task_lower)
            if count > best_count:
                best_count = count
                best_role = role

        if best_role and best_count >= 2:
            return best_role

        # Fall back to Haiku classification (cheap, fast)
        try:
            response = self.client.messages.create(
                model=HAIKU,
                max_tokens=64,
                system=self.system_prompt,
                messages=[{"role": "user", "content": task_description}],
            )
            text = next((b.text for b in response.content if b.type == "text"), "")
            data = json.loads(text)
            agent = data.get("agent", "builder")
            if agent in ROLES:
                return agent
        except Exception:
            pass

        return best_role or "builder"
