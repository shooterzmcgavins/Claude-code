import json
from typing import Optional, Callable

from config import Config, SONNET, MODEL_COSTS
from core.workspace import Workspace
from core.task import Task, TaskStatus, TaskStore
from core.events import EventLog
from .base import BaseAgent
from .roles import ROLES


def _summarize_input(inp: dict) -> str:
    if not inp:
        return ""
    parts = []
    for k, v in list(inp.items())[:2]:
        s = str(v)
        parts.append(f"{s[:50]!r}" if len(s) > 50 else repr(s))
    return ", ".join(parts)


def _to_openai_tools(anthropic_tools: list) -> list:
    """Convert @beta_tool objects to OpenAI function-calling format."""
    result = []
    for t in anthropic_tools:
        schema = t.model_dump() if hasattr(t, "model_dump") else dict(t)
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
        role_cfg = ROLES.get(role, {})
        self._system_prompt = role_cfg.get("system_prompt", f"You are the {role} agent.")
        self._tool_spec = role_cfg.get("tools", "all")

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @property
    def tools(self) -> list:
        from tools import get_tools
        return get_tools(self._tool_spec, self.workspace, self._approval_callback)

    def execute(self, task: Task, model: Optional[str] = None) -> str:
        task.status = TaskStatus.IN_PROGRESS
        task.agent = self.role
        self.task_store.save(task)
        self.events.log("task.started", {"title": task.title}, task_id=task.id, agent=self.role)

        if self.config.is_ollama:
            return self._execute_ollama(task)
        return self._execute_anthropic(task, model or SONNET)

    # ── Anthropic path ────────────────────────────────────────────────────────

    def _execute_anthropic(self, task: Task, model: str) -> str:
        print(f"\n[{task.id}] {self.role} starting — {model.split('-')[1]} (anthropic)")

        messages = [{"role": "user", "content": self._task_prompt(task)}]

        runner = self.client.beta.messages.tool_runner(
            model=model,
            max_tokens=self.config.max_tokens,
            system=[{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=self.tools,
            messages=messages,
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
                elif block.type == "tool_use":
                    tool_calls += 1
                    print(f"  ↳ {block.name}({_summarize_input(block.input)})", flush=True)
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
            raise ImportError("Install the openai package: pip install openai")

        model = self.config.ollama_model
        print(f"\n[{task.id}] {self.role} starting — {model} (ollama)")

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

            # Append assistant turn (convert to dict for mutability)
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

            if not msg.tool_calls:
                final_text = msg.content or ""
                if final_text:
                    print(f"\n  {self.role}: {final_text}", flush=True)
                break

            for tc in msg.tool_calls:
                tool_calls_total += 1
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                print(f"  ↳ {fn_name}({_summarize_input(args)})", flush=True)

                fn = tool_fn_map.get(fn_name)
                if fn:
                    try:
                        result = fn(**args)
                    except Exception as e:
                        result = f"Tool error: {e}"
                else:
                    result = f"Unknown tool: {fn_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

        self._finish(task, final_text, tool_calls_total, model, 0.0)
        return final_text

    # ── Shared ────────────────────────────────────────────────────────────────

    def _task_prompt(self, task: Task) -> str:
        return (
            f"**Task ID:** {task.id}\n"
            f"**Title:** {task.title}\n\n"
            f"{task.description}\n\n"
            f"When complete, call `write_report` to save your findings."
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
        cost_str = f"~${cost:.4f}" if cost else "local (no cost)"
        print(f"\n  ✓ {task.id} complete  |  {tool_calls} tool calls  |  {cost_str}")
        report_path = self.workspace.reports / f"{task.id}.md"  # type: ignore[attr-defined]
        if report_path.exists():
            print(f"  📄 report → workspace/reports/{task.id}.md")


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in MODEL_COSTS:
        return 0.0
    in_rate, out_rate = MODEL_COSTS[model]
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
