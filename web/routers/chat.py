import asyncio
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from core.task import Task
from web import state, chat_history
from agents.roles import AGENT_NAMES

router = APIRouter(prefix="/api/chat", tags=["chat"])
log = logging.getLogger(__name__)

_CONTEXT_WINDOW = 10  # recent messages passed as history in chat mode


# ── Direct chat ───────────────────────────────────────────────────────────────

class DirectChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/direct")
async def direct_chat(body: DirectChatRequest):
    """Direct conversational chat — no task created, no task engine involved."""
    session_id = body.session_id or chat_history.new_session_id()
    chats_dir = state.workspace.root / "chats"

    agent_name = body.agent if body.agent and body.agent in AGENT_NAMES else "builder"

    provider = state.config.provider
    model = state.config.ollama_model if state.config.is_ollama else "claude-sonnet-4-6"
    log.info("DIRECT_CHAT provider=%s model=%s persona=%s", provider, model, agent_name)

    history = chat_history.load(chats_dir, session_id)
    reply = await asyncio.get_running_loop().run_in_executor(
        state.executor,
        _direct_reply,
        body.message,
        agent_name,
        history,
    )

    chat_history.append(chats_dir, session_id, "user", body.message, agent=agent_name)
    chat_history.append(chats_dir, session_id, "assistant", reply, agent=agent_name)

    return {
        "reply": reply,
        "session_id": session_id,
        "agent": agent_name,
    }


def _direct_reply(message: str, agent_name: str, history: list) -> str:
    """Blocking direct LLM call — runs in executor thread."""
    provider = state.config.provider
    model = state.config.ollama_model if state.config.is_ollama else "claude-sonnet-4-6"
    system = (
        f"You are a helpful AI assistant ({agent_name} persona). "
        f"Provider: {provider}. Model: {model}. "
        "Reply conversationally and directly. "
        "Do not create tasks, files, or reports unless explicitly asked."
    )

    msgs: list[dict] = []
    for h in history[-_CONTEXT_WINDOW:]:
        if h.get("role") in ("user", "assistant"):
            msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": message})

    if state.config.is_ollama:
        try:
            from openai import OpenAI
        except ImportError:
            return "Error: openai package not installed (pip install openai)"
        try:
            client = OpenAI(base_url=f"{state.config.ollama_base_url}/v1", api_key="ollama")
            resp = client.chat.completions.create(
                model=state.config.ollama_model,
                messages=[{"role": "system", "content": system}] + msgs,
                max_tokens=state.config.max_tokens,
            )
            return resp.choices[0].message.content or "(no response)"
        except Exception as exc:
            return f"Ollama error: {exc}"
    else:
        try:
            import anthropic as _ant
            client = _ant.Anthropic(api_key=state.config.api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=state.config.max_tokens,
                system=system,
                messages=msgs,
            )
            return next((b.text for b in resp.content if b.type == "text"), "(no response)")
        except Exception as exc:
            return f"Anthropic error: {exc}"


# ── Task-mode chat (legacy — kept for session linkage) ────────────────────────

class TaskChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/task")
async def task_chat(body: TaskChatRequest):
    """Create a tracked task from the chat UI and link it to the session."""
    session_id = body.session_id or chat_history.new_session_id()
    chats_dir = state.workspace.root / "chats"

    agent_name = body.agent if body.agent and body.agent in AGENT_NAMES else None
    agent_name = agent_name or state.supervisor.route(body.message)

    task = Task.create(body.message)
    state.task_store.save(task)
    state.event_log.log("task.created", {"title": task.title}, task_id=task.id)
    chat_history.append(chats_dir, session_id, "user", body.message, task_id=task.id)

    def _on_complete(tid: str, sid: str, ag: str) -> None:
        t = state.task_store.load(tid)
        if t and t.result:
            chat_history.append(chats_dir, sid, "assistant", t.result, agent=ag, task_id=tid)

    def _run() -> None:
        state.run_agent(task.id, agent_name)
        _on_complete(task.id, session_id, agent_name)

    asyncio.get_running_loop().run_in_executor(state.executor, _run)
    return {
        "task_id": task.id,
        "session_id": session_id,
        "agent": agent_name,
    }


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions():
    chats_dir = state.workspace.root / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    return chat_history.list_sessions(chats_dir)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    from fastapi import HTTPException
    chats_dir = state.workspace.root / "chats"
    messages = chat_history.load(chats_dir, session_id)
    if not messages:
        raise HTTPException(404, f"Session {session_id!r} not found")
    return {"session_id": session_id, "messages": messages}


@router.get("/overview")
async def overview():
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
        "model": state.config.ollama_model if state.config.is_ollama else "claude-sonnet-4-6",
    }


def _count_events() -> int:
    total = 0
    for path in state.workspace.events.glob("*.jsonl"):
        try:
            total += path.read_text().count("\n")
        except Exception:
            pass
    return total
