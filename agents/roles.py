"""Keyword lists used for zero-cost task routing.

System prompts and full agent personalities are defined in
workspace/agents/*.md — edit those files to change agent behavior.
This module only keeps the keyword lists that let the supervisor route
tasks without making an API call.
"""

# Fallback keywords if the agent's .md file can't be read
DEFAULT_KEYWORDS: dict[str, list[str]] = {
    "builder": [
        "build", "code", "implement", "fix", "debug", "test", "refactor",
        "create", "write", "program", "develop", "script", "function", "class",
        "patch", "edit", "feature", "error", "bug",
    ],
    "research": [
        "research", "find", "search", "what is", "explain", "look up",
        "investigate", "analyze", "compare", "review", "survey", "gather",
        "document", "learn", "how does",
    ],
    "planner": [
        "plan", "design", "architect", "strategy", "roadmap", "outline",
        "structure", "organize", "breakdown", "approach", "steps", "workflow",
    ],
    "monitor": [
        "check", "status", "monitor", "watch", "report", "health", "log",
        "metrics", "dashboard", "audit", "inspect", "verify",
    ],
    "automation": [
        "automate", "automation", "pipeline", "schedule", "batch",
        "deploy", "ci", "cd", "hook", "trigger", "cron", "job",
    ],
}

# Canonical agent names — used for validation and discovery
AGENT_NAMES = list(DEFAULT_KEYWORDS.keys())

SUPERVISOR_FALLBACK_PROMPT = """\
You are the workspace supervisor. Route the request to the best specialist agent.

Agents: builder, research, planner, monitor, automation

Reply with ONLY JSON: {"agent": "<name>", "reason": "<one sentence>"}"""
