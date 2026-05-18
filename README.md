# Claude-code

A token-efficient autonomous AI agent — a lightweight alternative to OpenClaw that keeps costs low by routing tasks to the cheapest model capable of handling them.

## Cost strategy

| Model | $/1M in | $/1M out | Used for |
|-------|---------|----------|---------|
| Haiku 4.5 | $1 | $5 | Simple Q&A, lookups, quick tasks |
| Sonnet 4.6 | $3 | $15 | Explanations, code generation |
| Opus 4.7 | $5 | $25 | Complex analysis, architecture |

By default the agent caps at Sonnet — it never escalates to Opus unless you explicitly allow it with `--max-model opus`. Haiku handles most tasks for pennies.

Additional savings:
- **Prompt caching** on the system prompt (shared across every turn)
- **Context pruning**: when conversation exceeds 20 turns, old messages are summarized by Haiku and replaced with a compact summary
- **No classification overhead**: complexity routing uses keyword heuristics — zero extra API calls

## Features

- Autonomous task execution with tool use (web search, URL fetching, shell, file I/O)
- Tiered model routing with keyword-based complexity scoring
- Multi-platform bots: Slack, Discord, Telegram
- Interactive REPL with per-session cost tracking

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
# One-shot task (auto-routes to cheapest capable model)
python main.py "What is the current Python version?"

# Force a specific model
python main.py --model sonnet "Refactor this code to use async/await"

# Allow escalation up to Opus for hard tasks
python main.py --max-model opus "Architect a distributed caching system"

# Interactive REPL
python main.py -i

# Run as a Telegram bot
TELEGRAM_BOT_TOKEN=... python main.py --platform telegram
```

## Project layout

```
main.py              CLI entry point and platform runner
config.py            Config dataclass and model constants
agent/
  core.py            Agent class, TokenTracker
  router.py          Complexity scoring and model selection
  context.py         Context pruning via Haiku summarization
  tools.py           web_search, fetch_url, run_shell, read_file, write_file, list_files
platforms/
  base.py            Abstract Platform base class
  slack.py           Slack bot adapter
  discord.py         Discord bot adapter
  telegram.py        Telegram bot adapter
```

## Available tools

| Tool | Description |
|------|-------------|
| `web_search` | DuckDuckGo search |
| `fetch_url` | Fetch and extract text from any URL |
| `run_shell` | Run shell commands (30s timeout, blocks destructive patterns) |
| `read_file` | Read a file (capped at 5000 chars) |
| `write_file` | Write a file (creates parent dirs) |
| `list_files` | Glob-based directory listing |
