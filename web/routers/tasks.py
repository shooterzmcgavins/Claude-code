from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from core.task import Task, TaskStatus
from web import state

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    agent: Optional[str] = None


def _task_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "agent": task.agent,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "result": task.result,
        "tags": task.tags,
        "has_report": (state.workspace.reports / f"{task.id}.md").exists(),
    }


@router.get("")
async def list_tasks(status: Optional[str] = None, limit: int = 100):
    tasks = state.task_store.list_all()
    if status:
        try:
            s = TaskStatus(status)
            tasks = [t for t in tasks if t.status == s]
        except ValueError:
            raise HTTPException(400, f"Unknown status: {status}")
    return [_task_dict(t) for t in tasks[:limit]]


@router.post("", status_code=201)
async def create_task(body: TaskCreate):
    task = Task.create(body.title, body.description)
    state.task_store.save(task)
    state.event_log.log("task.created", {"title": task.title}, task_id=task.id)

    agent_name = body.agent or state.supervisor.route(task.description or task.title)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(state.executor, state.run_agent, task.id, agent_name)

    return {**_task_dict(task), "agent": agent_name}


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = state.task_store.load(task_id.upper())
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return _task_dict(task)
