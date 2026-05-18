from fastapi import APIRouter, HTTPException
from agents.loader import AgentLoader
from agents.roles import AGENT_NAMES
from core.task import TaskStatus
from web import state

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _agent_dict(name: str) -> dict:
    loader = AgentLoader(state.workspace.agents)
    cfg = loader.load(name)
    # Determine activity from recent in-progress tasks
    in_progress = state.task_store.list_by_status(TaskStatus.IN_PROGRESS)
    current_task = next((t.id for t in in_progress if t.agent == name), None)
    last_events = [e for e in state.event_log.recent(50) if e.get("agent") == name]
    last_activity = last_events[0].get("ts") if last_events else None
    return {
        "name": cfg.name,
        "role": cfg.role,
        "model": cfg.model,
        "tools": cfg.tools,
        "keywords": cfg.keywords,
        "source_file": cfg.source_file,
        "system_prompt": cfg.system_prompt,
        "status": "active" if current_task else "idle",
        "current_task": current_task,
        "last_activity": last_activity,
    }


@router.get("")
async def list_agents():
    return [_agent_dict(name) for name in AGENT_NAMES]


@router.get("/{name}")
async def get_agent(name: str):
    if name not in AGENT_NAMES:
        raise HTTPException(404, f"Agent {name!r} not found")
    return _agent_dict(name)
