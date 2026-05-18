import json
from typing import Optional, Callable

from config import Config, SONNET, MODEL_COSTS
from core.workspace import Workspace
from core.task import Task, TaskStatus, TaskStore
from core.events import EventLog
from .base import BaseAgent
from .loader import AgentLoader


def _summarize_input(inp: dict) -> str:
    if not inp:
        return ""
    parts = []
    for k, v in list(inp.items())[:2]:
        s = str(v)
        parts.append(f"{s[:50]!r}" if len(s) > 50 else repr(s))
    return ", ".join(parts)


def _to_openai_tools(anthropic_tools: list) -> list:
    result = []
    for t in anthropic_tools:
        try:
            schema = t.model_dump() if hasattr(t, "model_dump") else dict(t)
        except Exception:
            schema = {"name": t.__name__, "description": t.__doc__ or "", "input_schema": {}}
        result.append({
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema.get("description", ""),
                "parameters": schema.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return result


class SpecialistAgent(BaseAgent):
    def __init__(
        self,
        role: str,
        config: Config,
        workspace: Workspace,
        events: EventLog,
        task_store: TaskStore,
        approval_callback: Optional[Callable[[str, str, str], bool]] = None,
    ):
        super().__init__(config, workspace, events, task_store)
        self.role = role
        self.name = role
        self._approval_callback = approval_callback
        # Load personality and instructions from workspace/agents/<role>.md
        self._cfg = AgentLoader(workspace.agents).load(role)  # type: ignore[attr-defined]

    @property
    def system_prompt(self) -> str:
        return self._cfg.system_prompt

    @property
    def tools(self) -> list:
        from tools import get_tools
        return get_tools(self._cfg.tools, self.workspace, self._approval_callback)

    def execute(self, task: Task, model: Optional[str] = None) -> str:
        task.status = TaskStatus.IN_PROGRESS
        task.agent = self.role
        self.task_store.save(task)
        self.events.log("task.started", {"title": task.title}, task_id=task.id, agent=self.role)

        if self.config.is_ollama:
            return self._execute_ollama(task)
        return self._execute_anthropic(task, model or self._model())

    # ── Anthropic path ────────────────────────────────────────────────────────

    def _execute_anthropic(self, task: Task, model: str) -> str:
        print(f"\n[{task.id}] {self.role} starting — {model.split('-')[1]} (anthropic)")
        if self._cfg.source_file:
            print(f"  identity → {self._cfg.source_file}")

        runner = self.client.beta.messages.tool_runner(
            model=model,
            max_tokens=self.config.max_tokens,
            system=[{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=self.tools,
            messages=[{"role": "user", "content": self._task_prompt(task)}],
        )

        final_text = ""
        tool_calls = 0
        input_tokens = 0
        output_tokens = 0

        for message in runner:
            for block in message.content:
                if not hasattr(block, "type"):
                    continue
                if block.type == "text" and block.text:
                    print(f"\n  {self.role}: {block.text}", flush=True)
                    final_text = block.text
                    self.events.log("agent.message", {"text": block.text}, task_id=task.id, agent=self.role)
                elif block.type == "tool_use":
                    tool_calls += 1
                    summary = _summarize_input(block.input)
                    print(f"  ↳ {block.name}({summary})", flush=True)
                    self.events.log("agent.tool_call", {"tool": block.name, "args": summary}, task_id=task.id, agent=self.role)
            if hasattr(message, "usage") and message.usage:
                input_tokens += getattr(message.usage, "input_tokens", 0) or 0
                output_tokens += getattr(message.usage, "output_tokens", 0) or 0

        cost = _estimate_cost(model, input_tokens, output_tokens)
        self._finish(task, final_text, tool_calls, model, cost)
        return final_text

    # ── Ollama path ───────────────────────────────────────────────────────────

    def _execute_ollama(self, task: Task) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run: pip install openai")

        model = self.config.ollama_model
        print(f"\n[{task.id}] {self.role} starting — {model} (ollama)")
        if self._cfg.source_file:
            print(f"  identity → {self._cfg.source_file}")

        client = OpenAI(base_url=f"{self.config.ollama_base_url}/v1", api_key="ollama")
        tool_list = self.tools
        oai_tools = _to_openai_tools(tool_list)
        tool_fn_map = {t.__name__: t for t in tool_list}

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._task_prompt(task)},
        ]

        final_text = ""
        tool_calls_total = 0

        while True:
            kwargs: dict = {"model": model, "messages": messages, "max_tokens": self.config.max_tokens}
            if oai_tools:
                kwargs["tools"] = oai_tools

            response = client.chat.completions.create(**kwargs)
            msg = response.choices[0].message
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

            if not msg.tool_calls:
                final_text = msg.content or ""
                if final_text:
                    print(f"\n  {self.role}: {final_text}", flush=True)
                    self.events.log("agent.message", {"text": final_text}, task_id=task.id, agent=self.role)
                break

            for tc in msg.tool_calls:
                tool_calls_total += 1
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                summary = _summarize_input(args)
                print(f"  ↳ {fn_name}({summary})", flush=True)
                self.events.log("agent.tool_call", {"tool": fn_name, "args": summary}, task_id=task.id, agent=self.role)
                fn = tool_fn_map.get(fn_name)
                result = fn(**args) if fn else f"Unknown tool: {fn_name}"
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

        self._finish(task, final_text, tool_calls_total, model, 0.0)
        return final_text

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _model(self) -> str:
        from config import HAIKU, SONNET, OPUS
        mapping = {"haiku": HAIKU, "sonnet": SONNET, "opus": OPUS}
        return mapping.get(self._cfg.model, SONNET)

    def _task_prompt(self, task: Task) -> str:
        return (
            f"**Task ID:** {task.id}\n"
            f"**Title:** {task.title}\n\n"
            f"{task.description}\n\n"
            "When complete, call `write_report` to save your findings."
        )

    def _finish(self, task: Task, final_text: str, tool_calls: int, model: str, cost: float) -> None:
        task.status = TaskStatus.COMPLETE
        task.result = final_text
        self.task_store.save(task)
        self.events.log(
            "task.complete",
            {"tool_calls": tool_calls, "model": model, "cost_usd": round(cost, 5)},
            task_id=task.id,
            agent=self.role,
        )
        cost_str = f"~${cost:.4f}" if cost else "local (free)"
        print(f"\n  ✓ {task.id} complete  |  {tool_calls} tool calls  |  {cost_str}")
        report_path = self.workspace.reports / f"{task.id}.md"  # type: ignore[attr-defined]
        if report_path.exists():
            print(f"  📄 report → workspace/reports/{task.id}.md")


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in MODEL_COSTS:
        return 0.0
    in_rate, out_rate = MODEL_COSTS[model]
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
