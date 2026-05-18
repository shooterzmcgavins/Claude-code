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
        self.client = anthropic.Anthropic(api_key=config.api_key)

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def execute(self, task: Task, model: Optional[str] = None) -> str:
        raise NotImplementedError
