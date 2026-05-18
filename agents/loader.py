"""Load agent configuration from workspace/agents/*.md files at runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from core.markdown import parse_frontmatter, extract_section


@dataclass
class AgentConfig:
    name: str
    role: str
    model: str
    tools: Union[str, list]          # "all" or list of tool names
    keywords: list[str]
    system_prompt: str
    source_file: str = ""            # path to the .md file that was loaded


class AgentLoader:
    """Reads workspace/agents/{name}.md and returns an AgentConfig.

    Falls back to sensible defaults if the file is missing, so the system
    degrades gracefully rather than crashing.
    """

    def __init__(self, agents_dir: Path):
        self.dir = agents_dir

    def load(self, agent_name: str) -> AgentConfig:
        path = self.dir / f"{agent_name}.md"
        if path.exists():
            return self._parse(agent_name, path)
        return self._fallback(agent_name)

    def list_available(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.md"))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _parse(self, name: str, path: Path) -> AgentConfig:
        content = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)

        # System prompt lives in the "## System Prompt" section.
        # Fall back to the full body if the section is missing.
        system_prompt = extract_section(body, "System Prompt") or body.strip()

        keywords = meta.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]

        tools = meta.get("tools", "all")

        return AgentConfig(
            name=meta.get("name", name),
            role=meta.get("role", name.title()),
            model=meta.get("model", "sonnet"),
            tools=tools,
            keywords=keywords,
            system_prompt=system_prompt,
            source_file=str(path),
        )

    @staticmethod
    def _fallback(name: str) -> AgentConfig:
        return AgentConfig(
            name=name,
            role=name.title(),
            model="sonnet",
            tools="all",
            keywords=[],
            system_prompt=(
                f"You are the {name} agent working in the AI Engineering Workspace.\n"
                "Complete the assigned task and call `write_report` when done."
            ),
        )
