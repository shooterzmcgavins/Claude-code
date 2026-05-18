import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.task import Task
from web import state, chat_history
from agents.roles import AGENT_NAMES

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None    # None → supervisor routes
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    task_id: str
    session_id: str
    agent: str


@router.post("", response_model=ChatResponse)
async def send_message(body: ChatRequest):
    # Resolve session
    session_id = body.session_id or chat_history.new_session_id()

    # Determine agent
    agent_name = body.agent or "supervisor"
    if agent_name == "supervisor" or agent_name not in AGENT_NAMES:
        agent_name = state.supervisor.route(body.message)

    # Create task
    task = Task.create(body.message)
    state.task_store.save(task)
    state.event_log.log("task.created", {"title": task.title}, task_id=task.id)

    # Persist user message
    chats_dir = state.workspace.root / "chats"
    chat_history.append(chats_dir, session_id, "user", body.message, task_id=task.id)

    # Hook to save assistant reply when task completes
    def _on_complete(tid: str, sid: str, ag: str) -> None:
        t = state.task_store.load(tid)
        if t and t.result:
            chat_history.append(chats_dir, sid, "assistant", t.result, agent=ag, task_id=tid)

    # Run agent in thread pool
    def _run():
        state.run_agent(task.id, agent_name)
        _on_complete(task.id, session_id, agent_name)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(state.executor, _run)

    return ChatResponse(task_id=task.id, session_id=session_id, agent=agent_name)


@router.get("/sessions")
async def list_sessions():
    chats_dir = state.workspace.root / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    return chat_history.list_sessions(chats_dir)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    chats_dir = state.workspace.root / "chats"
    messages = chat_history.load(chats_dir, session_id)
    if not messages:
        raise HTTPException(404, f"Session {session_id!r} not found")
    return {"session_id": session_id, "messages": messages}


@router.get("/overview")
async def overview():
    """Stats for the Overview page."""
    import time
    from core.task import TaskStatus
    tasks = state.task_store.list_all()
    counts = {s.value: 0 for s in TaskStatus}
    for t in tasks:
        counts[t.status.value] += 1
    return {
        "task_counts": counts,
        "total_tasks": len(tasks),
        "event_count": _count_events(),
        "uptime_seconds": int(time.time() - state.start_time),
        "provider": state.config.provider,
        "model": state.config.ollama_model if state.config.is_ollama else "sonnet",
    }


def _count_events() -> int:
    total = 0
    for path in state.workspace.events.glob("*.jsonl"):
        try:
            total += path.read_text().count("\n")
        except Exception:
            pass
    return total
