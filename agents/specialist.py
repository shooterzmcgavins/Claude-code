from typing import Optional, Callable
from datetime import datetime

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
        model = model or SONNET
        task.status = TaskStatus.IN_PROGRESS
        task.agent = self.role
        self.task_store.save(task)
        self.events.log("task.started", {"title": task.title}, task_id=task.id, agent=self.role)

        print(f"\n[{task.id}] {self.role} starting — model: {model.split('-')[1]}")

        messages = [{
            "role": "user",
            "content": (
                f"**Task ID:** {task.id}\n"
                f"**Title:** {task.title}\n\n"
                f"{task.description}\n\n"
                f"When complete, call `write_report` to save your findings."
            ),
        }]

        runner = self.client.beta.messages.tool_runner(
            model=model,
            max_tokens=self.config.max_tokens,
            system=[{
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
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

        task.status = TaskStatus.COMPLETE
        task.result = final_text
        self.task_store.save(task)
        self.events.log(
            "task.complete",
            {"tool_calls": tool_calls, "model": model, "cost_usd": round(cost, 5)},
            task_id=task.id,
            agent=self.role,
        )

        report_path = self.workspace.reports / f"{task.id}.md"  # type: ignore[attr-defined]
        print(f"\n  ✓ {task.id} complete  |  {tool_calls} tool calls  |  ~${cost:.4f}")
        if report_path.exists():
            print(f"  📄 report → workspace/reports/{task.id}.md")

        return final_text


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in MODEL_COSTS:
        return 0.0
    in_rate, out_rate = MODEL_COSTS[model]
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
