from pathlib import Path

WORKSPACE_DIRS = [
    "tasks", "events", "memory", "reports",
    "agents", "workflows", "vault", "scripts", "dashboards",
]


class Workspace:
    def __init__(self, root: Path = Path("workspace")):
        self.root = root
        for name in WORKSPACE_DIRS:
            setattr(self, name, root / name)

    def init(self) -> None:
        for name in WORKSPACE_DIRS:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(
                "# Workspace\n\nThis directory is managed by the AI engineering workspace.\n\n"
                "## Layout\n"
                "- `tasks/` — task state files (JSON)\n"
                "- `events/` — append-only event log (JSONL, one file per day)\n"
                "- `memory/` — persistent agent memory (Markdown)\n"
                "- `reports/` — completed task reports (Markdown)\n"
                "- `agents/` — per-agent working files\n"
                "- `workflows/` — workflow definitions and state\n"
                "- `vault/` — config, credentials references, approval queue\n"
                "- `scripts/` — generated automation scripts\n"
                "- `dashboards/` — generated status dashboards\n"
            )
        for role in ["builder", "research", "planner", "monitor", "automation"]:
            agent_dir = self.agents / role  # type: ignore[attr-defined]
            agent_dir.mkdir(exist_ok=True)

    @classmethod
    def default(cls) -> "Workspace":
        return cls(Path("workspace"))
