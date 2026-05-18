"""Module-level app state shared across all routers.

Initialized once at server startup via init().
"""
from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config
    from core.workspace import Workspace
    from core.task import TaskStore
    from core.events import EventLog
    from agents.supervisor import Supervisor
    from web.approval import ApprovalManager

config: "Config"
workspace: "Workspace"
task_store: "TaskStore"
event_log: "EventLog"
supervisor: "Supervisor"
approval_manager: "ApprovalManager"
executor: ThreadPoolExecutor
start_time: float


def init(cfg, ws) -> None:
    global config, workspace, task_store, event_log, supervisor
    global approval_manager, executor, start_time

    from core.task import TaskStore
    from core.events import EventLog
    from agents.supervisor import Supervisor
    from web.approval import ApprovalManager

    config = cfg
    workspace = ws
    task_store = TaskStore(ws.tasks)
    event_log = EventLog(ws.events)
    supervisor = Supervisor(config, workspace, event_log, task_store)
    approval_manager = ApprovalManager()
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent")
    start_time = time.time()


def run_agent(task_id: str, agent_name: str) -> None:
    """Execute an agent task in the current thread (called via executor)."""
    from core.task import TaskStatus
    from agents.specialist import SpecialistAgent

    task = task_store.load(task_id)
    if not task:
        return

    def approval_cb(agent: str, _action: str, command: str) -> bool:
        return approval_manager.request_approval(agent, command, task_id)

    agent = SpecialistAgent(
        role=agent_name,
        config=config,
        workspace=workspace,
        events=event_log,
        task_store=task_store,
        approval_callback=approval_cb,
    )
    try:
        agent.execute(task)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.result = str(exc)
        task_store.save(task)
        event_log.log("task.failed", {"error": str(exc)}, task_id=task_id, agent=agent_name)
