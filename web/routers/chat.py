import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.task import Task
from web import state, chat_history
from agents.roles import AGENT_NAMES

router = APIRouter(prefix="/api/chat", tags=["chat"])
log = logging.getLogger(__name__)

_CONTEXT_WINDOW = 20  # messages of per-agent history to pass as context

# Supervisor has a routing-only system prompt in its .md file.
# In chat mode we use this conversational override instead.
_SUPERVISOR_CHAT_PROMPT = """\
You are the workspace supervisor — the central orchestrator of the AI Engineering Workspace.
You have a complete view of the workspace: its specialist agents, task history, memory, \
reports, and operational state.

Specialist agents available:
- builder — code, implementation, debugging, file editing
- research — web search, documentation, information gathering
- planner — goal decomposition, roadmaps, workflow design
- monitor — system health, log inspection, status checks
- automation — scripts, pipelines, CI/CD, scheduled jobs

In conversational chat mode you:
- Answer questions about the workspace, agents, and their capabilities
- Help the user decide which agent to use for a given task
- Summarize recent activity and explain workspace state
- Provide operational guidance and coordinate multi-step work

Be direct, helpful, and workspace-aware. Do not output routing JSON in chat mode.\
"""


# ── Direct chat ───────────────────────────────────────────────────────────────

class DirectChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None


@router.post("/direct")
async def direct_chat(body: DirectChatRequest):
    """Direct conversational chat — per-agent persistent history, no task created."""
    chats_dir = state.workspace.root / "chats"
    agent_name = body.agent if body.agent and body.agent in AGENT_NAMES else "supervisor"

    provider = state.config.provider
    model = state.config.ollama_model if state.config.is_ollama else "claude-sonnet-4-6"
    log.info("DIRECT_CHAT provider=%s model=%s agent=%s", provider, model, agent_name)

    history = chat_history.load_agent(chats_dir, agent_name)
    system = _build_chat_system(agent_name, provider, model)

    reply = await asyncio.get_running_loop().run_in_executor(
        state.executor,
        _call_llm,
        system,
        history,
        body.message,
    )

    chat_history.append_agent(chats_dir, agent_name, "user", body.message)
    chat_history.append_agent(chats_dir, agent_name, "assistant", reply)

    from agents.loader import AgentLoader
    agent_cfg = AgentLoader(state.workspace.agents).load(agent_name)
    identity_file = agent_cfg.source_file or f"workspace/agents/{agent_name}.md (default)"

    return {
        "reply": reply,
        "agent": agent_name,
        "agent_role": agent_cfg.role,
        "identity_file": identity_file,
        "provider": provider,
        "model": model,
    }


@router.get("/agent/{agent_name}")
async def get_agent_chat(agent_name: str):
    """Get the persistent conversation history for a named agent."""
    if agent_name not in AGENT_NAMES:
        raise HTTPException(404, f"Unknown agent: {agent_name!r}")
    chats_dir = state.workspace.root / "chats"
    messages = chat_history.load_agent(chats_dir, agent_name)
    from agents.loader import AgentLoader
    agent_cfg = AgentLoader(state.workspace.agents).load(agent_name)
    return {
        "agent": agent_name,
        "role": agent_cfg.role,
        "identity_file": agent_cfg.source_file or f"workspace/agents/{agent_name}.md (default)",
        "messages": messages,
        "message_count": len(messages),
    }


@router.get("/agents")
async def list_agent_chats():
    """Return conversation summary for every agent (for sidebar display)."""
    chats_dir = state.workspace.root / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    from agents.loader import AgentLoader
    loader = AgentLoader(state.workspace.agents)
    result = []
    for name in AGENT_NAMES:
        summary = chat_history.agent_summary(chats_dir, name)
        cfg = loader.load(name)
        summary["role"] = cfg.role
        result.append(summary)
    return result


def _build_chat_system(agent_name: str, provider: str, model: str) -> str:
    """Build a conversational system prompt for direct chat mode."""
    if agent_name == "supervisor":
        base = _SUPERVISOR_CHAT_PROMPT
    else:
        from agents.loader import AgentLoader
        agent_cfg = AgentLoader(state.workspace.agents).load(agent_name)
        base = agent_cfg.system_prompt

    workspace_ctx = _workspace_context()

    return (
        f"{base}\n\n"
        f"== Workspace Context ==\n"
        f"Provider: {provider}. Model: {model}.\n"
        f"{workspace_ctx}\n"
        f"== End Context ==\n\n"
        "You are in conversational chat mode. Reply directly and helpfully. "
        "Do not call tools, create tasks, or write reports unless the user explicitly asks."
    )


def _workspace_context() -> str:
    """Build compact workspace context string."""
    lines = []
    try:
        tasks = state.task_store.list_all()
        if tasks:
            recent = sorted(tasks, key=lambda t: getattr(t, "created_at", "") or "", reverse=True)[:5]
            lines.append("Recent tasks:")
            for t in recent:
                lines.append(f"  {t.id}: {t.title[:55]} [{t.status.value}]")
    except Exception:
        pass
    try:
        memory_dir = state.workspace.root / "memory"
        if memory_dir.exists():
            keys = [p.stem for p in sorted(memory_dir.glob("*.md"))]
            if keys:
                lines.append(f"Memory: {', '.join(keys)}")
    except Exception:
        pass
    try:
        reports_dir = state.workspace.root / "reports"
        if reports_dir.exists():
            count = len(list(reports_dir.glob("*.md")))
            if count:
                lines.append(f"Reports: {count} available")
    except Exception:
        pass
    return "\n".join(lines) if lines else "No workspace activity yet."


def _call_llm(system: str, history: list, message: str) -> str:
    """Blocking LLM call — runs in executor thread."""
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


# ── Task-mode chat ────────────────────────────────────────────────────────────

class TaskChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/task")
async def task_chat(body: TaskChatRequest):
    """Create a tracked task from the chat UI."""
    session_id = body.session_id or chat_history.new_session_id()
    chats_dir = state.workspace.root / "chats"

    agent_name = body.agent if body.agent and body.agent in AGENT_NAMES else None
    # Don't route to supervisor as a task executor — fall back to builder
    if agent_name == "supervisor":
        agent_name = None
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


# ── Session endpoints (kept for task-mode history) ────────────────────────────

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
