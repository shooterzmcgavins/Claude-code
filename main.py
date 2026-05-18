#!/usr/bin/env python3
"""AI Engineering Workspace — interactive ops console."""
import sys
import os
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config import Config, HAIKU, SONNET, OPUS
from core.workspace import Workspace
from core.task import Task, TaskStore, TaskStatus
from core.events import EventLog
from agents.supervisor import Supervisor
from agents.specialist import SpecialistAgent
from agents.loader import AgentLoader
from agents.roles import AGENT_NAMES

MODEL_ALIASES = {"haiku": HAIKU, "sonnet": SONNET, "opus": OPUS}
BANNER = """\
╔══════════════════════════════════════════════╗
║        AI Engineering Workspace              ║
║  type a task, or /help for commands          ║
╚══════════════════════════════════════════════╝"""

HELP_TEXT = """\
Commands:
  <task description>       Create and run a task (e.g. "build a CSV parser")
  /status [TASK-ID]        Show all tasks, or details for one task
  /agents [name]           List agents, or inspect one agent's loaded config
  /log [n]                 Show recent events (default 20)
  /report TASK-ID          Print a task report
  /memory [key]            Read a memory entry (omit key to list all)
  /tasks [status]          Filter tasks by status (pending/complete/failed)
  /agents [name]           List agents, or show one agent's loaded identity
  /approve                 Review and act on pending shell command approvals
  /help                    Show this help
  /quit or Ctrl-C          Exit"""


class WorkspaceConsole:
    def __init__(self, config: Config, workspace: Workspace, force_model: str = None):
        self.config = config
        self.workspace = workspace
        self.task_store = TaskStore(workspace.tasks)  # type: ignore[arg-type]
        self.events = EventLog(workspace.events)  # type: ignore[arg-type]
        self.supervisor = Supervisor(config, workspace, self.events, self.task_store)
        self.force_model = force_model
        self._session_cost = 0.0
        self._pending_approvals: list[dict] = []

    def _approval_callback(self, agent: str, action: str, details: str) -> bool:
        print(f"\n  ⚠  [{agent}] wants to run shell command:")
        print(f"     $ {details}")
        try:
            answer = input("  Allow? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        return answer in ("y", "yes")

    def _run_task(self, description: str) -> None:
        task = Task.create(description)
        self.task_store.save(task)
        self.events.log("task.created", {"title": description}, task_id=task.id)

        agent_name = self.supervisor.route(description)
        model = self.force_model or SONNET
        print(f"\n  → routing to: {agent_name}  [{task.id}]")

        agent = SpecialistAgent(
            role=agent_name,
            config=self.config,
            workspace=self.workspace,
            events=self.events,
            task_store=self.task_store,
            approval_callback=self._approval_callback,
        )
        try:
            agent.execute(task, model=model)
        except KeyboardInterrupt:
            task.status = TaskStatus.FAILED
            task.result = "Interrupted by user"
            self.task_store.save(task)
            print(f"\n  Interrupted — {task.id} marked failed")

    def _cmd_status(self, args: str) -> None:
        args = args.strip()
        if args:
            task = self.task_store.load(args)
            if not task:
                print(f"  Task not found: {args}")
                return
            print(f"\n  {task.status_line()}")
            if task.description != task.title:
                print(f"\n  Description:\n  {task.description}")
            if task.result:
                print(f"\n  Result:\n  {task.result[:400]}")
            report = self.workspace.reports / f"{task.id}.md"  # type: ignore[attr-defined]
            if report.exists():
                print(f"\n  Report: workspace/reports/{task.id}.md")
        else:
            tasks = self.task_store.list_all()
            if not tasks:
                print("  No tasks yet.")
                return
            print()
            for t in tasks[:30]:
                print(f"  {t.status_line()}")
            if len(tasks) > 30:
                print(f"  ... and {len(tasks) - 30} more")

    def _cmd_agents(self, args: str = "") -> None:
        loader = AgentLoader(self.workspace.agents)  # type: ignore[attr-defined]
        name = args.strip().lower()
        if name and name in AGENT_NAMES:
            cfg = loader.load(name)
            print(f"\n  {cfg.name} — {cfg.role}")
            print(f"  model: {cfg.model}  |  tools: {cfg.tools}")
            src = cfg.source_file or "(built-in fallback)"
            print(f"  source: {src}")
            print(f"\n  System prompt preview:\n")
            for line in cfg.system_prompt.splitlines()[:12]:
                print(f"    {line}")
            if len(cfg.system_prompt.splitlines()) > 12:
                print("    ...")
        else:
            print()
            for agent_name in AGENT_NAMES:
                cfg = loader.load(agent_name)
                src = "✓" if cfg.source_file else "⚠ fallback"
                print(f"  {agent_name:<12}  {cfg.role:<22}  {src}")

    def _cmd_log(self, args: str) -> None:
        try:
            n = int(args.strip()) if args.strip() else 20
        except ValueError:
            n = 20
        entries = self.events.recent(n)
        if not entries:
            print("  No events yet.")
            return
        print()
        for e in reversed(entries):
            print(f"  {self.events.format_entry(e)}")

    def _cmd_report(self, args: str) -> None:
        task_id = args.strip().upper()
        if not task_id:
            print("  Usage: /report TASK-XXXXXX")
            return
        report = self.workspace.reports / f"{task_id}.md"  # type: ignore[attr-defined]
        if not report.exists():
            print(f"  No report found for {task_id}")
            return
        print()
        print(report.read_text())

    def _cmd_memory(self, args: str) -> None:
        key = args.strip()
        memory_dir = self.workspace.memory  # type: ignore[attr-defined]
        if not key:
            files = list(memory_dir.glob("*.md"))
            if not files:
                print("  No memory entries yet.")
                return
            print("\n  Memory keys:")
            for f in sorted(files):
                print(f"    - {f.stem}")
        else:
            path = memory_dir / f"{key}.md"
            if not path.exists():
                print(f"  No memory entry for '{key}'")
                return
            print()
            print(path.read_text())

    def _cmd_tasks(self, args: str) -> None:
        status_filter = args.strip().lower()
        all_tasks = self.task_store.list_all()
        if status_filter:
            try:
                status = TaskStatus(status_filter)
                all_tasks = [t for t in all_tasks if t.status == status]
            except ValueError:
                print(f"  Unknown status: {status_filter}. Use: pending, in_progress, complete, failed")
                return
        if not all_tasks:
            print("  No matching tasks.")
            return
        print()
        for t in all_tasks:
            print(f"  {t.status_line()}")

    def dispatch(self, line: str) -> bool:
        """Handle one input line. Returns False if the user wants to quit."""
        line = line.strip()
        if not line:
            return True

        if line.lower() in ("/quit", "/exit", "quit", "exit"):
            return False

        if line.startswith("/"):
            parts = line[1:].split(None, 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd in ("help", "h", "?"):
                print(HELP_TEXT)
            elif cmd == "status":
                self._cmd_status(args)
            elif cmd == "agents":
                self._cmd_agents(args)
            elif cmd == "log":
                self._cmd_log(args)
            elif cmd == "report":
                self._cmd_report(args)
            elif cmd == "memory":
                self._cmd_memory(args)
            elif cmd == "tasks":
                self._cmd_tasks(args)
            elif cmd == "approve":
                print("  Approval queue is managed inline — you'll be prompted when the agent needs it.")
            elif cmd == "cost":
                print("  (Cost tracking per task is logged in /log events)")
            else:
                print(f"  Unknown command: /{cmd}  — try /help")
        else:
            self._run_task(line)

        return True

    def run_repl(self) -> None:
        print(BANNER)
        tasks = self.task_store.list_all()
        print(f"  workspace: {self.workspace.root}  |  tasks: {len(tasks)}\n")

        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not self.dispatch(line):
                break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Engineering Workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Interactive REPL
  python main.py "build a CSV parser"         # One-shot task
  python main.py --model opus "architect..."  # Force model
  python main.py --workspace /path/to/ws      # Custom workspace
        """,
    )
    parser.add_argument("task", nargs="?", help="Task to run (omit for interactive REPL)")
    parser.add_argument("--model", "-m", choices=["haiku", "sonnet", "opus"],
                        help="Force a specific model for all tasks")
    parser.add_argument("--workspace", "-w", default="workspace",
                        help="Workspace directory (default: ./workspace)")
    parser.add_argument("--platform", choices=["slack", "discord", "telegram"],
                        help="Run as a bot on the specified platform")
    args = parser.parse_args()

    config = Config()
    workspace = Workspace(Path(args.workspace))
    workspace.init()

    force_model = MODEL_ALIASES.get(args.model) if args.model else None
    console = WorkspaceConsole(config, workspace, force_model=force_model)

    if args.platform:
        _run_platform(console, args.platform, config)
    elif args.task:
        console._run_task(args.task)
    else:
        console.run_repl()


def _run_platform(console: WorkspaceConsole, platform_name: str, config: Config) -> None:
    import asyncio

    async def handler(user_id: str, message: str) -> str:
        loop = asyncio.get_event_loop()
        task = Task.create(message)
        console.task_store.save(task)
        agent_name = console.supervisor.route(message)
        agent = SpecialistAgent(
            role=agent_name,
            config=config,
            workspace=console.workspace,
            events=console.events,
            task_store=console.task_store,
        )
        result = await loop.run_in_executor(None, agent.execute, task)
        return result or f"Task {task.id} complete — no text response."

    if platform_name == "slack":
        from platforms import SlackPlatform
        platform = SlackPlatform(config.slack_token or "")
    elif platform_name == "discord":
        from platforms import DiscordPlatform
        platform = DiscordPlatform(config.discord_token or "")
    elif platform_name == "telegram":
        from platforms import TelegramPlatform
        platform = TelegramPlatform(config.telegram_token or "")
    else:
        print(f"Unknown platform: {platform_name}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting {platform_name} bot...")
    asyncio.run(platform.start(handler))


if __name__ == "__main__":
    main()
