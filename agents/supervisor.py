import json

from config import Config, HAIKU
from core.workspace import Workspace
from core.task import Task, TaskStore
from core.events import EventLog
from .base import BaseAgent
from .loader import AgentLoader
from .roles import DEFAULT_KEYWORDS, AGENT_NAMES, SUPERVISOR_FALLBACK_PROMPT


class Supervisor(BaseAgent):
    name = "supervisor"

    def __init__(self, config: Config, workspace: Workspace, events: EventLog, task_store: TaskStore):
        super().__init__(config, workspace, events, task_store)
        self._loader = AgentLoader(workspace.agents)  # type: ignore[attr-defined]
        self._cfg = self._loader.load("supervisor")

    @property
    def system_prompt(self) -> str:
        return self._cfg.system_prompt

    def route(self, task_description: str) -> str:
        """Route a task description to the best agent. Returns the agent name."""
        task_lower = task_description.lower()

        # Build keyword map: prefer keywords from the loaded .md files
        keyword_map: dict[str, list[str]] = {}
        for name in AGENT_NAMES:
            cfg = self._loader.load(name)
            keyword_map[name] = cfg.keywords if cfg.keywords else DEFAULT_KEYWORDS.get(name, [])

        # Zero-cost keyword scoring
        scores = {role: sum(1 for kw in kws if kw in task_lower) for role, kws in keyword_map.items()}
        best_role, best_score = max(scores.items(), key=lambda x: x[1])

        if best_score >= 2:
            return best_role

        # LLM fallback — cheap routing call
        try:
            if self.config.is_ollama:
                return self._route_ollama(task_description)
            return self._route_anthropic(task_description)
        except Exception:
            pass

        return best_role if best_score >= 1 else "builder"

    def _route_anthropic(self, task: str) -> str:
        response = self.client.messages.create(
            model=HAIKU,
            max_tokens=64,
            system=self.system_prompt,
            messages=[{"role": "user", "content": task}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        agent = json.loads(text).get("agent", "builder")
        return agent if agent in AGENT_NAMES else "builder"

    def _route_ollama(self, task: str) -> str:
        from openai import OpenAI
        client = OpenAI(base_url=f"{self.config.ollama_base_url}/v1", api_key="ollama")
        response = client.chat.completions.create(
            model=self.config.ollama_model,
            max_tokens=64,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": task},
            ],
        )
        text = response.choices[0].message.content or ""
        agent = json.loads(text).get("agent", "builder")
        return agent if agent in AGENT_NAMES else "builder"
