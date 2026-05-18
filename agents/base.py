from abc import ABC, abstractmethod
from typing import Optional
import anthropic

from config import Config
from core.workspace import Workspace
from core.task import Task, TaskStore
from core.events import EventLog


class BaseAgent(ABC):
    name: str = "base"

    def __init__(
        self,
        config: Config,
        workspace: Workspace,
        events: EventLog,
        task_store: TaskStore,
    ):
        self.config = config
        self.workspace = workspace
        self.events = events
        self.task_store = task_store
        # Only instantiate the Anthropic client when an API key is available.
        # anthropic.Anthropic(api_key="") raises AuthenticationError at construction
        # time in SDK ≥0.40, which would immediately kill every task on the Ollama path.
        self._anthropic_client: Optional[anthropic.Anthropic] = None
        if config.api_key:
            self._anthropic_client = anthropic.Anthropic(api_key=config.api_key)

    @property
    def client(self) -> anthropic.Anthropic:
        if self._anthropic_client is None:
            raise RuntimeError(
                "Anthropic client is not configured. "
                "Set ANTHROPIC_API_KEY or switch PROVIDER to 'anthropic'."
            )
        return self._anthropic_client

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def execute(self, task: Task, model: Optional[str] = None) -> str:
        raise NotImplementedError
